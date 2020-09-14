#!/usr/bin/env python
import sys, logging
import re
import sqlite3
import binascii
import gsm0338
import code
from optparse import OptionParser

db_revision = 0

def cs(l, exit = 0):
    code.interact(local = dict(globals(), **l) )
    if exit == 1:
        exit()

def unpackSeptets(septets, numberOfSeptets=None, prevOctet=None, shift=7):
    """ Unpacks the specified septets into octets 
    (From https://github.com/faucamp/python-gsmmodem)
    
    :param septets: Iterator or iterable containing the septets packed into octets
    :type septets: iter(bytearray), bytearray or str
    :param numberOfSeptets: The amount of septets to unpack (or None for all remaining in "septets")
    :type numberOfSeptets: int or None
    
    :return: The septets unpacked into octets
    :rtype: bytearray
    """
    result = bytearray()
    if type(septets) == str:
        septets = iter(bytearray(septets))
    elif type(septets) == bytearray:
        septets = iter(septets)     
    if numberOfSeptets == None:     
        numberOfSeptets = sys.maxint # Loop until StopIteration
    i = 0
    for octet in septets:
        i += 1
        if shift == 7:
            shift = 1 
            if prevOctet != None:
                result.append(prevOctet >> 1)
            if i <= numberOfSeptets:
                result.append(octet & 0x7F)
                prevOctet = octet          
            if i == numberOfSeptets:       
                break
            else:
                continue
        b = ((octet << shift) & 0x7F) | (prevOctet >> (8 - shift))
        
        prevOctet = octet
        result.append(b) 
        shift += 1
        
        if i == numberOfSeptets:
            break
    if shift == 7:
        b = prevOctet >> (8 - shift)
        if b:
            # The final septet value still needs to be unpacked
            result.append(b)        
    return result


def _dbd_decode_bin(s):
    """
    https://sourceforge.net/p/libdbi/libdbi/ci/master/tree/src/dbd_helper.c#l457
    """
    if len(s) == 0:
        return 'NO_MSG'
    offset = ord(s[0])
    out = []
    for i in range (1, len(s)):
        if s[i] >= 0:
            if s[i-1] == 1 and ( s[i] == 1 or s[i] == 2 or s[i] == 27 ):
                continue
            #Convert each 0x01 0x01 sequence into a single character 0x00.
            #Convert 0x01 0x02 into 0x01.  Convert 0x01 0x28 into 0x27.
            if s[i] == 1 and ( s[i+1] == 1 or s[i+1] == 2 or s[i+1] == 27 ):
                c = s[i+1] - 1
            else:
                c = s[i]
        x = (256 + ord(c) + offset) % 256
        if x < 256:
            out.append(chr(x))
    rstr = ''.join(out)
    return rstr

def parse_udh(s):
    if len(s) != 6:
        return False
    udh = {}
    udh['len'] = ord(s[0])
    udh['iei'] = ord(s[1])
    udh['header_len'] = ord(s[2])
    udh['csms_ref'] = ord(s[3])
    udh['parts'] = ord(s[4])
    udh['part_num'] = ord(s[5])
    return udh

def read_queue(q_id = 0, unsent = False, sent = False, where = '', src = '', dest = '',
               both=None, negate = False, limit = 0, order = False, nosys = False):
    global db_revision
    try:
        smsc_db_conn = sqlite3.connect(sms_db)
        smsc_db_cursor = smsc_db_conn.cursor()
        smsc_db_conn.text_factory = str
        sql = "SELECT value FROM Meta WHERE key='revision'"
        smsc_db_cursor.execute(sql)
        _revision = smsc_db_cursor.fetchone()
        db_revision = _revision[0]
        sql = 'SELECT * from SMS WHERE id > 0 '
        if not (sent and unsent):
            if unsent == True:
                sql = sql + ' AND sent is NULL '
            if sent == True:
                sql = sql + ' AND sent is not NULL '
        if q_id > 1:
            sql = sql + ' AND ('
            for i in q_id.split(','):
                sql = sql + 'id=' + str(i) + ' OR '
            sql = sql[:-4]
            sql = sql + ')'
        if where != '':
            sql = sql + ' AND ' + where
        if negate:
            op = "!="
        else:
            op = "="
        if src != '':
            sql = sql + ' AND src_addr' + op + '"' + src + '"'
        if dest != '':
            sql = sql + ' AND dest_addr' + op + '"' + dest + '"'
        if both:
            sql = sql + ' AND (src_addr like "%' + both + '%" OR dest_addr like "%' + both + '%")'
        if nosys:
            sql = sql + ' AND src_ton != 5'
        if order == False:
            sql = sql + ' ORDER BY created ASC '
        else:
            sql = sql + ' ORDER BY created DESC '
        if limit > 0:
            sql = sql + ' LIMIT ' + limit
        log.debug(sql)
        smsc_db_cursor.execute(sql)
        _sms = smsc_db_cursor.fetchall()
        smsc_db_conn.close()
        return _sms
    except sqlite3.Error as sqlerror:
        smsc_db_conn.close()
        raise Exception('Oops. SQL error: %s, %s' % (sqlerror.args[0], sql))

def build_msgs(smsq):
    ret = []
    csms = {}
    for sms in smsq:
        charset='utf-8'
        utext=''
        """
        
        0        id INTEGER PRIMARY KEY AUTOINCREMENT
        1        created TIMESTAMP NOT NULL
        2        sent TIMESTAMP
        3        deliver_attempts INTEGER NOT NULL DEFAULT 0
        4        valid_until TIMESTAMP
        5        reply_path_req INTEGER NOT NULL
        6        status_rep_req INTEGER NOT NULL
        (7       is_report INTEGER NOT NULL)
        (8       msg_ref INTEGER NOT NULL)
        7 9      protocol_id INTEGER NOT NULL
        8 10     data_coding_scheme INTEGER NOT NULL
        9 11     ud_hdr_ind INTEGER NOT NULL
        10 12    src_addr TEXT NOT NULL
        11 13    src_ton INTEGER NOT NULL
        12 14    src_npi INTEGER NOT NULL
        13 15    dest_addr TEXT NOT NULL
        14 16    dest_ton INTEGER NOT NULL
        15 17    dest_npi INTEGER NOT NULL
        16 18    user_data BLOB
        17 19    header BLOB
        18 20    text TEXT
        """
        if db_revision == '5':
          reg_delivery = sms[6]
          is_report = sms[7]
          coding = sms[10]
          udhdr = sms[11]
          src = sms[12]
          ston = sms[13]
          dest = sms[15]
          userdata = sms[18]
          header = sms[19]
          text = sms[20]
        elif db_revision == '4':
          reg_delivery = 0
          is_report = 0
          coding = sms[8]   
          udhdr = sms[9]
          src = sms[10]
          ston = sms[11]
          dest = sms[13]
          coding = sms[8]
          userdata = sms[16]
          header = sms[17]
          text = sms[18]
        else:
            print "Unknown DB Revision"
            exit()

        log.debug("Message ID: \033[93m" + str(sms[0]) + '\033[0m')
        log.debug("Is Report: " + str(is_report))
        log.debug("Valid Until: " + str(sms[4]))
        log.debug("Coding is \033[32m%s \033[0m" % str(coding))
        log.debug("UD HDR Indicator: " + str( sms[9] ))
        log.debug("User Data: " + binascii.hexlify( userdata ))
        
        dtext = _dbd_decode_bin(userdata)

        if udhdr == 64:
            h = dtext[:7]
            #for i in [0, 1, 2, 3, 4, 5, 6]:
            #    log.debug( ord(h[i]) )
            #udh=parse_udh(h)
            udhdr = 1
        
        if (udhdr == 1 and ord(dtext[0]) == 5):
            log.debug("UDH Detected")
            h = dtext[:6]
            msg = dtext[6:]                   
            udh = parse_udh(h)
            log.debug("CSMS Reference: " + str(udh['csms_ref']))
            log.debug("Part No #" + str(udh['part_num']) + " of " + str(udh['parts']))
            log.debug("Part Coding:" + str(coding))
            not_decoded = 0
            if coding == 0:
                msg = str(unpackSeptets(msg,None,0,6).lstrip(chr(0)).rstrip(chr(0)))
                try:
                    msgpart = unicode(msg,'gsm03.38')
                    charset = 'GSM03.38'
                except:
                    log.debug("Multipart decode failed for gsm03.38")
            else:
                try:
                    msgpart = unicode(msg,'utf-8')
                    charset = 'UTF-8'
                except UnicodeDecodeError:
                    log.debug("Multipart decode failed for UTF-8")
                    try:
                        msgpart = unicode(msg,'utf-16be')
                        charset = 'UTF-16BE'
                    except:
                        # Can't decode this segment on its own,
                        # probably because truncated utf16 data.
                        msgpart = msg
                        charset = 'utf-16be'
                        not_decoded = 1
                        if udh['part_num'] > 1 and csms[udh['csms_ref']]['not_decoded'][udh['part_num']-1] == 1:
                            # try adding it to the last part..
                            csms[udh['csms_ref']]['text'][udh['part_num']-1] += msg
                            msgpart = ''

            if not_decoded == 1:
                log.debug("Message Part Not Decoded on its own")
            else:
                log.debug("Message Part:" + msgpart.encode('utf-8','replace'))
            try:
                if not udh['csms_ref'] in csms or csms[udh['csms_ref']] == None:
                    csms[udh['csms_ref']] = {}
                    csms[udh['csms_ref']]['ids'] = {}
                    csms[udh['csms_ref']]['text'] = {}
                    csms[udh['csms_ref']]['not_decoded'] = {}
                    csms[udh['csms_ref']]['parts'] = udh['parts']
                csms[udh['csms_ref']]['ids'][udh['part_num']] = sms[0]
                csms[udh['csms_ref']]['text'][udh['part_num']] = msgpart
                csms[udh['csms_ref']]['not_decoded'][udh['part_num']] = not_decoded

                if csms[udh['csms_ref']]['parts'] and udh['part_num'] == csms[udh['csms_ref']]['parts']:
                    log.debug("Found Last Part of CSMS %s" % str(udh['csms_ref']))
                    utext = ''
                    mid = ''
                    for i in range (0, csms[udh['csms_ref']]['parts']):
                        try:
                            if csms[udh['csms_ref']]['not_decoded'][i+1] == 1:
                                text += csms[udh['csms_ref']]['text'][i+1]
                            else:   
                                utext += csms[udh['csms_ref']]['text'][i+1]
                            mid += str(csms[udh['csms_ref']]['ids'][i+1]) + ', '
                        except KeyError:
                            log.error("Missing part %s of Multipart SMS %s for id %s" 
                            % ((i+1), udh['csms_ref'], sms[0]) )
                            pass
                    #if csms[udh['csms_ref']]['not_decoded'][i] == 1:
                    #    utext=utext+text.decode(charset)
                    mid = mid.rstrip(', ')
                    csms[udh['csms_ref']] = None
                    #utext = unicode(utext.encode('utf-8'))
                else:
                    continue
            except Exception as ex:
                print ex
        else:
            mid = str(sms[0])
            if coding == 0:
                # unpackSeptets returns bytearray
                text7 = unpackSeptets(dtext).rstrip(chr(0))
                log.debug ("User Data Octets unpacked: " + binascii.hexlify(text7))
                # gsm_codec_s = gsm0338.Codec()
                gsm_codec = gsm0338.Codec(single_shift_decode_map=gsm0338.SINGLE_SHIFT_CHARACTER_SET_SPANISH)
                utext = gsm_codec.decode(str(text7))[0]
                charset = 'gsm03.38'
            elif (coding == 8 or coding == 4) and is_report < 1:
                # I don't have any indicator of what the actual charset is.
                log.debug ("Lost")
                try:
                    if re.match(r'[\x00-\x0f]', dtext):
                        utext = unicode(dtext,'utf-16be')
                        charset = 'UTF-16BE'
                    else:    
                        utext = unicode(dtext,'utf-8')
                        charset = 'UTF-8'
                    
                except UnicodeDecodeError as e:
                    try:
                        utext = unicode(dtext,'utf-16be')
                    except Exception as e:
                        print e
                    charset = 'UTF-16BE'
                log.debug ("Coding value is 4/8, Charset Determined %s", charset)
            else:
                utext = unicode(dtext,charset,'replace')
                charset = 'utf-8'
                
        log.debug("User Data dbd_decoded: " + binascii.hexlify(utext.encode(charset,'replace')))

        if header:
            log.debug("Header field: " + binascii.hexlify(header))

        log.debug("DB text field '%s' (Length:%s)" % ( binascii.hexlify(text), str(len(text) )))
    
        r = {}
        r['sms'] = sms
        r['mid'] = mid
        r['src'] = src
        r['ston'] = ston
        r['dest'] = dest
        r['coding'] = coding
        r['charset'] = charset
        r['text'] = utext
        r['created'] = sms[1]
        r['is_report'] = is_report
        r['reg_delivery'] = reg_delivery
        ret.append(r)
        if 'options' in globals() and options.debug_stop:
          cs(locals())
          
    return ret

def display_queue(smsq):
    n = 0
    for item in smsq:
        sms = item['sms']
        mid = item['mid']
        utext = item['text']        
        charset = item['charset']
        src = item['src']
        ston = item['ston']
        dest = item['dest']
        coding = item['coding']
        n = n + 1
        text1 = ''
        parts = str(mid.count(',')+1)
        if not options.brief:
            print "\033[34m------------------------------------\033[0m"
            print "SMSQ ID: " + mid
            print "Created: " + sms[1]
            print "From: " + src +  " to: "  + dest
            if sms[2] is not None:
                print "Sent: " + str(sms[2])
            else:
                print "Delivery Attempts: " + str(sms[3])
            if item['is_report'] == 1:
                print "-----> Is Report"
            else:
                print "Coding, Charset: " + str(coding) + ',' + charset
                print "Parts: " + parts
            if item['reg_delivery'] == 1:
                print "Delivery Report Requested"
        try:
            if options.unicode:
                text1 = utext.encode('unicode_escape')
            elif options.coding:
                text1 = utext.encode(options.coding)
            else:
                text1 = utext.encode('utf-8')
        except:
            e = sys.exc_info()[0]
            print 'Caught Exception Encoding: %s %s on Line %s' % (e, sys.exc_info()[1], sys.exc_info()[2].tb_lineno)
            
        if options.brief:
            if item['is_report'] == 1:
                charset = "\033[96mREPORT\033[0m"
            if options.colour:
                idc=str(91+int(parts))
                textc = '96' if sms[2] is None else '92'
                textb = '0;03' if ston is 5 else '1'
                fromc = '1;89' if ston is 5 else '95'
                if options.both == src[-5:]:
                    textc = '94'
                    src = src[:6]+'\033[93m'+src[6:]+'\033[0m'
                if options.both == dest[-5:]:
                    dest = dest[:6]+'\033[93m'+dest[6:]+'\033[0m'
                print ( '\033[%sm%s\033[0m \033[%sm%s\033[0m \033[91m%s\033[0m %s \033[%s;%sm%s \033[0m'
                % ( idc, sms[0], fromc, src.ljust(11), dest.ljust(11), charset.ljust(8), textb, textc, text1[:100] ) )
            else:
                print sms[0], src.ljust(11), dest.ljust(11), charset.ljust(8), text1[:100]
        else:    
            print ('\033[93mSMS:\033[0m ('+ str(len(text1)) + ') [ \033[1;31m'
            +text1+
            ' \033[0m ]')
            print "\033[34m------------------------------------\033[0m\n"
    print str(n)+" SMS messages were displayed"

def display_queue_summary(smsq):
    total = len(smsq)
    unsent = 0
    delivered = 0
    for i in range(0, total):
        if smsq[i][2] is None:
            unsent = unsent + 1
        else:
            delivered = delivered + 1
    print '    ---- OSMO SMS Queue ----'
    print '    Sent Messages: %s' % delivered
    print '    Undelivered Messages: %s' % unsent
    print '    Total Messages: %s' % total
    print '    Oldest Message: %s' % smsq[0][1]
    print '    Newest Message: %s' % smsq[total-1][1]

if __name__ == '__main__':
    parser = OptionParser()
    unsent =  False
    sent = False  
    parser.add_option("-p", "--sms-db", dest="sms_db",
        help="Specify SMS database (default is /var/lib/osmocom/hlr.sqlite3)")
    parser.add_option("-q", "--show-queue", dest="showq", action="store_true",
        help="Display Summary Information about the Osmo SMS Queue")
    parser.add_option("-i", "--id", dest="msgid",
        help="Display a single Message from the SMS Queue")
    parser.add_option("-u", "--unsent", dest="unsent", action="store_true",
        help="Include pending messages")
    parser.add_option("-s", "--sent", dest="sent", action="store_true",
        help="Include sent messages")
    parser.add_option("-b", "--brief", dest="brief", action="store_true",
        help="Display Brief (One Line) Format")
    parser.add_option("-c", "--colour", dest="colour", action="store_true",
        help="Colourise Brief Format")
    parser.add_option("-U", "--unicode", dest="unicode", action="store_true",
        help="Output Unicode Sequences")
    parser.add_option("-C", "--coding", dest="coding",
            help="Coding to use for display")        
    parser.add_option("-f", "--from", dest="src", default='',
            help="Filter on from (src_addr)")
    parser.add_option("-t", "--to", dest="dest", default='',
            help="Filter on to (dest_addr)")                    
    parser.add_option("-B", "--both", dest="both", default='',
            help="Filter on both (with like match)")
    parser.add_option("-n", "--negate", dest="negate", action="store_true",
            help="Negate to/from search")        
    parser.add_option("-N", "--no-system", dest="nosys", action="store_true",
            help="Don't display message from system (TON ALPHA)")
    parser.add_option("-w", "--where", dest="where", default='',
        help="Specify SQL where condition")
    parser.add_option("-l", "--limit", dest="limit", default=0,
        help="Specify SQL Limit")    
    parser.add_option("-r", "--reverse", dest="order", action="store_true", default=False,
        help="Reverse Sort Order")   
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Turn on debug output")
    parser.add_option("-D", "--debug-stop", dest="debug_stop", action="store_true",
        help="Stop and Shell with msg")        
    (options, args) = parser.parse_args()

    if options.sms_db:
        sms_db = options.sms_db
    else:
        sms_db = '/var/lib/osmocom/hlr.sqlite3'

    logging.basicConfig(stream=sys.stderr)
    if options.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    log = logging.getLogger('SmsQ')
    log.setLevel(loglevel)
    if options.showq:
        smsq = read_queue()
        display_queue_summary(smsq)
        exit()
    if options.msgid:
        smsq = read_queue(options.msgid)
        msgs=build_msgs(smsq)        
        display_queue(msgs)
    else:
        smsq = read_queue(0, options.unsent, options.sent, options.where, options.src, options.dest, options.both, options.negate, options.limit, options.order, options.nosys)
        msgq=build_msgs(smsq)
        display_queue(msgq)
