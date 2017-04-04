#!/usr/bin/env python
import sys, logging
import re
import sqlite3
import binascii
import gsm0338
import code
from optparse import OptionParser


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

def read_queue(q_id = 0, unsent = False, sent = False, where = '', src = '', dest = '', negate = False, limit = 0, order = False):
    try:
        sq_hlr = sqlite3.connect(sq_hlr_path)
        sq_hlr_cursor = sq_hlr.cursor()
        sq_hlr.text_factory = str
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
            sql = sql + ' AND src_addr' + op + src
        if dest != '':
            sql = sql + ' AND dest_addr' + op + dest
        if order == False:
            sql = sql + ' ORDER BY created ASC '
        else:
            sql = sql + ' ORDER BY created DESC '
        if limit > 0:
            sql = sql + ' LIMIT ' + limit
	log.debug(sql)
        sq_hlr_cursor.execute(sql)
        _sms = sq_hlr_cursor.fetchall()
        sq_hlr.close()
        return _sms
    except sqlite3.Error as sqlerror:
        sq_hlr.close()
        raise Exception('SQ_HLR error: %s' % sqlerror.args[0])

def build_msgs(smsq):
    ret = []
    csms = {}
    for sms in smsq:
        utext=''
        #code.interact(local=locals())
        coding = sms[8]
        udhdr = sms[9]
        userdata = sms[16]
        header = sms[17]
        text = sms[18]
        
        dtext = _dbd_decode_bin(userdata)

        if udhdr == 64:
            #h = dtext[:7]
            #for i in [0, 1, 2, 3, 4, 5, 6]:
            #    log.debug( ord(h[i]) )
            #msg = text[7:]
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
            try:
                msgpart = unicode(msg,'utf-8')
                charset = 'UTF-8'
            except UnicodeDecodeError:
                try:
                    msgpart = unicode(msg,'utf-16be','replace')
                    charset = 'UTF-16BE'
                except:
                    code.interact(local=locals())
            log.debug("Message Part:" + msgpart.encode('utf-8','replace'))
            try:
                if not udh['csms_ref'] in csms or csms[udh['csms_ref']] == None:
                    csms[udh['csms_ref']] = {}
                    csms[udh['csms_ref']]['ids'] = {}
                    csms[udh['csms_ref']]['text'] = {}
                    csms[udh['csms_ref']]['parts'] = udh['parts']
                    csms[udh['csms_ref']]['ids'][udh['part_num']] = sms[0]
                    csms[udh['csms_ref']]['text'][udh['part_num']] = msgpart
                else:
                    csms[udh['csms_ref']]['ids'][udh['part_num']] = sms[0]
                    csms[udh['csms_ref']]['text'][udh['part_num']] = msgpart

                if csms[udh['csms_ref']]['parts'] and udh['part_num'] == csms[udh['csms_ref']]['parts']:
                    log.debug("Found Last Part of CSMS %s" % str(udh['csms_ref']))
                    utext = ''
                    mid = ''
                    for i in range (0, csms[udh['csms_ref']]['parts']):
                        try:
                            utext += csms[udh['csms_ref']]['text'][i+1]
                            mid += str(csms[udh['csms_ref']]['ids'][i+1]) + ', '
                        except KeyError:
                            log.error("Missing part %s of Multipart SMS %s for id %s" 
                            % ((i+1), udh['csms_ref'], sms[0]) )
                    mid = mid.rstrip(', ')
                    #code.interact(local=locals())
                    csms[udh['csms_ref']] = None
                    utext = utext.encode('utf-8') 
                else:
                    continue
            except Exception as ex:
                print ex
                code.interact(local=locals())
        else:
            mid = str(sms[0])
            utext = dtext

        log.debug("Message ID: \033[93m" + str(sms[0]) + '\033[0m')
        log.debug("Valid Until: " + str(sms[4]))
        log.debug("Coding is \033[32m%s \033[0m" % str(coding))
        log.debug("UD HDR Indicator: " + str( sms[9] ))
        log.debug("User Data: " + binascii.hexlify( userdata ))
        log.debug("User Data dbd_decoded: " + binascii.hexlify(utext))
        # FIXME: have seen multipart messages with different charsets in each part.
        if coding == 0:
            utext7 = unpackSeptets(utext).rstrip(chr(0)) 
            log.debug ("User Data Octets unpacked: " + binascii.hexlify(utext7))
            utext = unicode(utext7)
            gsm_codec = gsm0338.Codec(single_shift_decode_map=gsm0338.SINGLE_SHIFT_CHARACTER_SET_SPANISH)
            utext = gsm_codec.decode(utext)[0]
            charset = 'gsm03.38'
        if coding == 8 or coding == 4:
            # I don't have any indicator of what the actual charset is.
            try:
                utext = unicode(utext,'utf-8')
                charset = 'UTF-8'
                utext = re.sub(r'[^\x01-\xFF]', '', utext) 
            except UnicodeDecodeError:
                utext = unicode(utext,'utf-16be')
                charset = 'UTF-16BE'
            log.debug ("Coding value is 4/8, Charset Determined %s", charset)            
        if header:
            log.debug("Header field: " + binascii.hexlify(header))

        log.debug("DB text field '%s' (Length:%s)" % ( binascii.hexlify(text), str(len(text) )))
    
        r = {}
        r['sms'] = sms
        r['mid'] = mid
        r['charset'] = charset
        r['text'] = utext
        ret.append(r)
        
    return ret

def display_queue(smsq):
    n = 0
    for item in smsq:
        sms = item['sms']
        mid = item['mid']
        utext = item['text']        
        charset = item['charset']
        src = sms[10]
        dest = sms[13]
        coding = sms[8]
        n = n + 1
        text1 = ''
        if not options.brief:
            print "\033[34m------------------------------------\033[0m"
            print "SMSQ ID: " + mid
            print "Created: " + sms[1]
            print "From: " + src +  " to: "  + dest 
            if sms[2] is not None:
                print "Sent: " + str(sms[2])
            else:
                print "Delivery Attempts: " + str(sms[3])
            print "Charset:" + charset
        try:
            if options.unicode:
                text1 = utext.encode('unicode_escape')
            elif options.coding:
                text1 = utext.encode(options.coding)
            else:
                text1 = utext.encode('utf-8')
        except:
            e = sys.exc_info()[0]
            print 'Caught Exception Encoding: %s %s %s' % (e, sys.exc_info()[1], sys.exc_info()[2].tb_lineno)
            code.interact(local=locals())
            
        if options.brief:
            if options.colour:
                print (
                '\033[93m%s\033[0m \033[95m%s\033[0m \033[91m%s\033[0m %s \033[1;92m%s \033[0m' 
                % ( sms[0], src.ljust(11), dest.ljust(11), charset.ljust(8), text1[:100] ) )
            else:
                print sms[0], src.ljust(11), dest.ljust(11), charset.ljust(8), text1[:100]
        else:    
            print ('\033[93mSMS:\033[0m [ \033[1;31m '
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
    parser.add_option("-p", "--sql-path", dest="sq_hlr_path",
        help="Specify SQLITE hlr path (default is /var/lib/osmocom/hlr.sqlite3)")
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
    parser.add_option("-n", "--negate", dest="negate", action="store_true",
            help="Negate to/from search")        
    parser.add_option("-w", "--where", dest="where", default='',
        help="Specify SQL where condition")
    parser.add_option("-l", "--limit", dest="limit", default=0,
        help="Specify SQL Limit")    
    parser.add_option("-r", "--reverse", dest="order", action="store_true", default=False,
        help="Reverse Sort Order")   
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Turn on debug output")
    (options, args) = parser.parse_args()

    if options.sq_hlr_path:
        sq_hlr_path = options.sq_hlr_path
    else:
        sq_hlr_path = '/var/lib/osmocom/hlr.sqlite3'

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
    if options.msgid:
        smsq = read_queue(options.msgid)
        q=build_msgs(smsq)        
        display_queue(q)
    else:
        smsq = read_queue(0, options.unsent, options.sent, options.where, options.src, options.dest, options.negate, options.limit, options.order)
        q=build_msgs(smsq)
        display_queue(q)
