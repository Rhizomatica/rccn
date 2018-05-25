#!/usr/bin/env python 
# -*- coding: utf-8 -*-
############################################################################
# 
# Copyright (C) 2013 tele <tele@rhizomatica.org>
# Copyright (C) 2017 Keith Whyte <keith@rhizomatica.org>
#
# SMS module
# This file is part of RCCN
#
# RCCN is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RCCN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

import sys
sys.path.append("..")
from config import *

import urllib, obscvty, time
from subscriber import Subscriber, SubscriberException 
from numbering import Numbering, NumberingException
from threading import Thread
import ESL
import binascii
import gsm0338
import smpplib
import smpplib.gsm


class SMSException(Exception):
    pass

class SMS:

    def __init__(self):

        self.server = kannel_server
        self.port = kannel_port
        self.username = kannel_username
        self.password = kannel_password
        self.smssvc_url = smssvc_url
        self.smssvc_user = smssvc_user
        self.smssvc_secret = smssvc_secret
        self.smssvc_from = smssvc_from
        self.charset = 'UTF-8'
        self.coding = 2
        self.context = 'SMS_LOCAL'
        self.source = ''
        self.destination = ''
        self.internal_destination = ''
        self.text = ''
        self.save_sms = 1

        self.numbering = Numbering()

    def filter(self):
        if self.destination in extensions_list:
            return False
        if len(self.destination) < 5:
            sms_log.info('Dropping SMS on floor because destinaton: %s' % self.destination)
            return True
        if self.charset=='8-BIT' and len(self.destination) < 7:
            sms_log.info('Dropping 8-BIT SMS with destinaton: %s' % self.destination)
            return True
        drop_regexp = ['simchautosynchro.+','DSAX[0-9]+ND','Activate:dt=','REG-REQ?v=3;','^GWDR']
        for regexp in drop_regexp:
            if re.search(regexp,self.text):
                sms_log.info('Dropping SMS on floor because text matched %s' % regexp)
                return True
        return False

    def route_intl_service(self, source, destination, text, sequence):
        sms_log.info('SMS for delivery by provider: %s %s %s %s' % (source, destination, text, sequence))
        
        _from = { '52' : '529512058046', }.get(destination[:2], self.smssvc_from)
        # These values are for nexmo
        values = {  'api_key': self.smssvc_user,
                    'api_secret': self.smssvc_secret,
                    'from': _from, 
                    'to': destination, 
                    'text': text, 
                }
        data = urllib.urlencode(values)
        t = Thread (target = self._t_urlopen2, args = (self.smssvc_url, data) )
        t.start()
        sms_log.info('Started Remote SMS Delivery Thread')
        if self.save_sms:
            sms_log.info('Save SMS in the history')
            self.save(source, destination, self.context)
        return 0

    def route_to_hfconnector(self, src, dest, msg, seq, direction):
        _hermes_path = '/var/spool/' + direction + '_messages/'
        try:
            if not os.path.exists(_hermes_path):
                os.makedirs(_hermes_path)
            _sms_file = _hermes_path + "msg-" + str(seq) + '.txt'
            with open(_sms_file, "w") as file:
                file.write("{0}\n".format(str(src)))
                file.write("{0}\n".format(str(dest)))
                file.write("{0}\n".format(str(msg)))
            log.debug('Wrote SMS to %s' % _sms_file)
            return 0
        except Exception as e:
            log.debug(e)
            return -1        


    def receive(self, source, destination, text, charset, coding, seq):
        self.charset = charset
        self.coding = coding
        self.source = source
        self.text = text
        self.internal_destination = destination
        if destination.find('+') > 1:
            destination = destination.split('+')[0]
        self.destination = destination

        sms_log.info('Received SMS: %s %s %s %s %s' % (source, destination, text, charset, coding))	
        #sms_log.info(binascii.hexlify(text))
        # SMS_LOCAL | SMS_INTERNAL | SMS_INBOUND | SMS_OUTBOUND | SMS_ROAMING

        # some seemingly autogenerated SMS we just want to drop on the floor:
        try:
            if self.filter():
                return
        except Exception as e:
            api_log.info('Caught an Error in sms:filter %s' % e)
            pass

        if use_sip == 'yes':
            try:
                sip_endpoint=self.numbering.is_number_sip_connected_no_session(self.destination)
            except Exception as e:
                sms_log.info('SIP Exception: %s' % e)

            sms_log.info('SIP SMS? %s' % sip_endpoint)

            if sip_endpoint:
                m=re.compile('sofia/([a-z]*)/sip:(.*)').search(sip_endpoint)

                if m:
                    sip_profile=m.group(1)
                    contact=(m.group(2))
                    s=contact.split(';')
                    # Get fs_path param.
                    r=re.compile('^fs_path=')
                    s=filter(r.match,s)

                    if len(s)>0: # Have fs_path
                        bracket=re.compile('fs_path=%3C(.*)%3E').search(s[0])
                        if bracket:
                            params=urllib.unquote(bracket.group(1)).split(';')
                            path=params[0].replace('sip:','')
                            r=re.compile('received=*')
                            rec=filter(r.match,params)
                            received=rec[0].replace('received=sip:','')
                        else:
                            path=s[0]
                            received = urllib.unquote(path).split('=')[1].split('@')[1]
                    else:
                        received = 'None'

                if sip_profile == 'internalvpn':
                    simple_dest=self.destination+'@'+vpn_ip_address
                    if path == '10.23.0.14':
                        self.source = self.source+'@sip.rhizomatica.org'
                        simple_dest=self.destination+'@10.23.0.14'+';received='+received
                else:
                    simple_dest=sip_profile+'/'+contact
                try:
                    con = ESL.ESLconnection("127.0.0.1", "8021", "ClueCon")
                    event = ESL.ESLevent("CUSTOM", "SMS::SEND_MESSAGE")
                    sms_log.info('SMS to SIP: Source is %s' % self.source)
                    sms_log.info('SMS to SIP: Dest: %s' % simple_dest)
                    sms_log.info('SMS to SIP: Received: %s' % received)
                    sms_log.info('Text: %s' % self.text.decode(charset,'replace'))
                    sms_log.info('Text: %s' % type(self.text))
                    sms_log.info('Coding: %s' % self.coding)
                    event.addHeader("from", self.source)
                    event.addHeader("to", simple_dest)
                    event.addHeader("sip_profile", sip_profile);
                    event.addHeader("dest_proto", "sip")
                    event.addHeader("type","text/plain")
                    if self.coding == '0':
                        msg=self.text.decode('utf8','replace')
                    else:
                        msg=self.text.decode(charset,'replace')
                    sms_log.info('Type: %s' % type(msg))
                    sms_log.info('Text: %s' % msg)
                    event.addBody(msg.encode(charset,'replace'))
                    con.sendEvent(event)
                    return
                except Exception as e:
                    api_log.info('Caught Error in sms sip routine: %s' % e)

        try:
            # auth checks
            # get auth info
            sub = Subscriber()

            # check if source or destination is roaming
            try:
                if self.numbering.is_number_roaming(source):
                # FIXME: ^^ Returns False for unregistered or unknown numbers.
                    sms_log.info('Source number is roaming')
                    self.roaming('caller')
		    return
            except NumberingException as e:
                sms_log.info('Sender unauthorized send notification message (exception)')
                self.context = 'SMS_UNAUTH'
                self.coding = 2
                self.send(config['smsc'], source, config['sms_source_unauthorized'])
                return

            try:
                if self.numbering.is_number_roaming(destination):
                    sms_log.info('Destination number is roaming')
                    self.roaming('called')
                    return
            except NumberingException as e:
                sms_log.info('Destination unauthorized send notification message')
                self.context = 'SMS_UNAUTH'
                self.send(config['smsc'], source, config['sms_destination_unauthorized'])
                return

            try:
                source_authorized = sub.is_authorized(source, 0)
            except SubscriberException as e:
                source_authorized = False
            try:
                destination_authorized = sub.is_authorized(destination, 0)
            except SubscriberException as e:
                destination_authorized = False

            if destination == self.smssvc_from:
                source_authorized = True
                destination_authorized = True
                # TODO. Make some kind of a map here.
                if incoming_intl_to_queue == 'yes':
                    self.route_to_hfconnector(source, destination, text, seq, 'incoming')
                    return
                else:    
                    destination = '68000122465'
                    intl = True
                

            sms_log.info('Source_authorized: %s Destination_authorized: %s' % (str(source_authorized), str(destination_authorized)))


            if not source_authorized and not self.numbering.is_number_internal(source):
                sms_log.info('Sender unauthorized send notification message (EXT)')
                self.context = 'SMS_UNAUTH'
                self.coding = 2
                self.send(config['smsc'], source, config['sms_source_unauthorized'])
                return

            if self.numbering.is_number_local(destination):
                sms_log.info('SMS_LOCAL check if subscriber is authorized')
                # get auth info
                sub = Subscriber()
                source_authorized = sub.is_authorized(source, 0)
                destination_authorized = sub.is_authorized(destination, 0)
                try:
                    if source_authorized and destination_authorized:
                        sms_log.info('Forward SMS back to BSC')
                        # number is local send SMS back to SMSc
                        self.context = 'SMS_LOCAL'
                        # Decision was not to send coding on here.....
                        self.send(source, destination, text, charset, 'utf-8', config['local_ip'], intl)
                    else:
                        if not self.numbering.is_number_local(source) and destination_authorized:
                            sms_log.info('SMS_INTERNAL Forward SMS back to BSC')
                            self.context = 'SMS_INTERNAL'
                            self.send(source, destination, text, charset, config['local_ip'], intl)
                        else:
                            if destination_authorized and not self.numbering.is_number_local(source):
                                sms_log.info('SMS_INBOUND Forward SMS back to BSC')
                                # number is local send SMS back to SMSc
                                self.context = 'SMS_INBOUND'
                                self.send(source, destination, text, charset)
                            else:
                                self.charset = 'UTF-8'
                                self.coding = 2
                                self.save_sms = 0
                                self.context = 'SMS_UNAUTH'
                                if not source_authorized and len(destination) != 3:
                                    sms_log.info('Sender unauthorized send notification message')
                                    self.send(config['smsc'], source, config['sms_source_unauthorized'])
                                else:
                                    sms_log.info('Destination unauthorized inform sender with a notification message')
                                    self.send(config['smsc'], source, config['sms_destination_unauthorized'])

                except SubscriberException as e:
                    raise SMSException('Receive SMS error: %s' % e)
            else:
        
                # dest number is not local, check if dest number is a shortcode
                if destination in extensions_list:
                    sms_log.info('Destination number is a shortcode, execute shortcode handler')
                    extension = importlib.import_module('extensions.ext_'+destination, 'extensions')
                    try:
                        sms_log.debug('Exec shortcode handler')
                        extension.handler('', source, destination, text)
                    except ExtensionException as e:
                        raise SMSException('Receive SMS error: %s' % e)
                else:
                    # check if sms is for another location
                    if self.numbering.is_number_internal(destination) and len(destination) == 11:
                        sms_log.info('SMS is for another site')
                        try:
                            site_ip = self.numbering.get_site_ip(destination)
                            sms_log.info('Send SMS to site IP: %s' % site_ip)
                            self.context = 'SMS_INTERNAL'
                            self.send(source, destination, text, self.charset, site_ip)
                        except NumberingException as e:
                            raise SMSException('Receive SMS error: %s' % e)
                    elif len(destination) != 3:
                        # dest number is for an external number send sms to sms provider
                        self.context = 'SMS_OUTBOUND'
                        sms_log.info('SMS is for an external number send SMS to SMS provider')
                        self.send(config['smsc'], source, 'Lo sentimos, destino '+str(destination)+ ' no disponible', 'utf-8')
                    else:
                        sms_log.info('SMS for %s was dropped' % destination)

        except NumberingException as e:
            raise SMSException('Receive SMS Error: %s' % e)
    
    def send(self, source, destination, text, charset='utf-8', server=config['local_ip'], intl=False):
        sms_log.info('SMS Send: Text: <%s> Charset: %s INTL:%s' % (text, charset, intl) )
        try:
            # In the case of single/broadcast from RAI, there's no charset passed and
            # the str is unicode
            sms_log.info('Type of text: %s', (type(text)) )
            if (charset == 'UTF-8' or charset == 'utf-8' or charset == 'gsm03.38') and type(text) != unicode:
                sms_log.info('1 case')
                str_text=unicode(text,charset).encode('utf-8')
            elif charset == 'UTF-16BE' and type(text) == unicode:
                sms_log.info('2 case')
                str_text=text.encode('utf-8')
                self.charset='UTF-8'
                self.coding = 2
            elif charset == 'unicode':
                sms_log.info('3 case')
                try:
                    str_text = text.encode('utf-8')
                    self.charset = 'UTF-8'
                except:
                    sms_log.error('UTF-8 encode failed')
                    str_text = text.encode('utf-16be')
                    self.charset = 'UTF-16BE'
            else:
                sms_log.info('4 case')
                str_text=text.encode('utf-8','replace')
                
            sms_log.info('Type str_text: %s', (type(str_text)) )

            if type(text) != unicode:
                try:
                    try:
                        # Test if we can encode this as GSM03.38
                        gsm_codec = gsm0338.Codec()
                        test=gsm_codec.decode(text)[0]
                        #test = text.encode('gsm03.38')
                        sms_log.debug('GSM03.38! %s -> %s' % (text, test))
                        self.coding = 0
                    except:
                        sms_log.debug('Using GSM03.38 default alphabet not possible. %s' % sys.exc_info()[1] )
                        import code
                        #code.interact(local = dict(globals(), **locals()) )
                    # Maybe we can see if we use the Spanish Char Set?
                    gsm_shift_codec = gsm0338.Codec(single_shift_decode_map=gsm0338.SINGLE_SHIFT_CHARACTER_SET_SPANISH)
                    test = gsm_shift_codec.encode(text)
                    # OK Passed, but still kannel will replace not default alphabet with '?'
                    coding = 2
                except:
                    sms_log.debug('Using GSM03.38 Spanish Shift not possible. %s' % sys.exc_info()[1] )
                    self.coding = 2
            enc_text = urllib.urlencode({'text': str_text })
        except:
            sms_log.info('Encoding Error: %s Line:%s' % (sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
            # Was still dropping messages here because we go on without defining enc_text
            # Some phones are sending multipart messages with distinct charsets.
            # kannel concatenates but sends the charset of 1st part (I think)
            # Make best effort to send something now that kannel won't puke on.
            str_text=text.decode('UTF-8','replace').encode('utf-8')
            self.charset='UTF-8'
            enc_text = urllib.urlencode({'text': str_text})
            self.coding = 2

        if server == config['local_ip']:
            try:
                if use_kannel == 'no' and source == '10000':
                    source = network_name
                sms_log.info('Send SMS to Local: %s %s %s %s' % (source, destination, text, enc_text))
                self.local_smpp_submit_sm(source, destination, text, intl)
                if self.save_sms:
                    sms_log.info('Save SMS in the history')
                    self.save(source, destination, self.context)
            except SMSException as e:
                raise SMSException("Error with local sumbit_sm")
        else:
            try:
                sms_log.info('Send SMS to %s: %s %s %s' % (server, source, destination, str_text))
                if "+" not in self.internal_destination:
                    destination = destination + '+1'
                else:
                    s = self.internal_destination.split('+')
                    destination = s[0] + '+' + str(int(s[1]) + 1)
                    if s[1] > 4:
                        sms_log.error("SMS is LOOPING!!")
                values = {'source': source, 'destination': destination, 'charset': self.charset, 'coding': self.coding, 'text': str_text, 'btext': '', 'dr': '', 'dcs': ''}
                data = urllib.urlencode(values)
                t = Thread (target = self._t_urlopen, args = (server, data) )
                t.start()
                sms_log.info('Started Remote RAPI Thread')
                if self.save_sms:
                    sms_log.info('Save SMS in the history')
                    self.save(source, destination, self.context)
            except IOError:
                raise SMSException('Error sending SMS to site %s' % server)
    
    def determine_coding(self, unicode_str):
        try:
            try:
                # Test if we can encode this as GSM03.38
                gsm_codec = gsm0338.Codec()
                tst=gsm_codec.encode(unicode_str)[0]
                sms_log.debug('GSM03.38! %s -> %s' % (unicode_str, tst))
                return smpplib.consts.SMPP_ENCODING_DEFAULT
            except:
                sms_log.debug('Enocoding to GSM03.38 default alphabet not possible. %s' % sys.exc_info()[1] )
            # Maybe we can see if we use the Spanish Char Set?
            gsm_shift_codec = gsm0338.Codec(single_shift_decode_map=gsm0338.SINGLE_SHIFT_CHARACTER_SET_SPANISH)
            tst = gsm_shift_codec.encode(unicode_str)[0]
            sms_log.debug('GSM03.38 Spanish! %s -> %s' % (unicode_str, gsm_shift_codec.decode(tst)[0]))
            return smpplib.consts.SMPP_ENCODING_DEFAULT
        except:
            sms_log.debug('Using GSM03.38 Spanish Shift not possible. %s' % sys.exc_info()[1] )
            return smpplib.consts.SMPP_ENCODING_ISO10646

    def local_smpp_submit_sm(self, source, destination, text, intl):
        if use_kannel == 'yes':
            try:
                enc_text = urllib.urlencode({'text': text})
                kannel_post="http://%s:%d/cgi-bin/sendsms?username=%s&password=%s&charset=%s&coding=%s&to=%s&from=%s&%s"\
                    % (self.server, self.port, self.username, self.password, self.charset, self.coding, destination, source, enc_text)
                sms_log.info('Kannel URL: %s' % (kannel_post))
                res = urllib.urlopen(kannel_post).read()
                sms_log.info('Kannel Result: %s' % (res))
                return
            except IOError:
                raise SMSException('Error connecting to Kannel to send SMS')
        try:
            if intl == True:
                ston = smpplib.consts.SMPP_TON_INTL
                snpi = smpplib.consts.SMPP_NPI_ISDN
            else:
                snpi = smpplib.consts.SMPP_NPI_UNK
                ston = smpplib.consts.SMPP_TON_ALNUM
            parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(text)
            smpp_client = smpplib.client.Client("127.0.0.1", 2775, 90)
            smpp_client.connect()
            smpp_client.bind_transceiver(system_id="OSMPP", password="Password")
            for part in parts:
                pdu = smpp_client.send_message(
                    source_addr_ton = ston,
                    source_addr_npi= snpi,
                    source_addr = str(source),
                    dest_addr_ton = smpplib.consts.SMPP_TON_SBSCR,
                    dest_addr_npi = smpplib.consts.SMPP_NPI_ISDN,
                    destination_addr = str(destination),
                    data_coding = encoding_flag,
                    esm_class = msg_type_flag,
                    short_message = part,
                    registered_delivery = False,
                )
            smpp_client.unbind()
            smpp_client.disconnect()
            del pdu
            del smpp_client
        except IOError:
            raise SMSException('Unable to Submit Message via SMPP')

    def roaming(self, subject):
        
        self.numbering = Numbering()
        self.subscriber = Subscriber()

        if subject == 'caller':
            # calling number is roaming 
            # check if destination number is roaming as well
            if self.numbering.is_number_roaming(self.destination):
                # well destination number is roaming as well send SMS to current_bts where the subscriber is roaming
                try:
                    current_bts = self.numbering.get_current_bts(self.destination)
                    sms_log.info('Destination number is roaming send SMS to current_bts: %s' % current_bts)
                    if current_bts == config['local_ip']:
                        log.info('Current bts same as local site send call to local Kannel')
                        self.context = 'SMS_ROAMING_LOCAL'
                        self.send(self.source, self.destination, self.text, self.charset)
                    else:
                        # send sms to destination site
                        self.context = 'SMS_ROAMING_INTERNAL'
                        self.send(self.source, self.destination, self.text, self.charset, current_bts)
                except NumberingException as e:
                    sms_log.error(e)
            else:
                # destination is not roaming check if destination if local site
                if self.numbering.is_number_local(self.destination) and len(self.destination) == 11:
                    sms_log.info('Destination is a local number')

                    if self.subscriber.is_authorized(self.destination, 0):
                        sms_log.info('Send sms to local kannel')
                        self.context = 'SMS_ROAMING_LOCAL'
                        self.send(self.source, self.destination, self.text)
                    else:
                        # destination cannot receive SMS inform source
                        self.context = 'SMS_ROAMING_UNAUTH'
                        self.receive(config['smsc'], source, config['sms_destination_unauthorized'], self.charset, self.coding)
                else:
                    # number is not local check if number is internal
                    if self.numbering.is_number_internal(self.destination) and len(self.destination) == 11:
                        # number is internal send SMS to destination site
                        current_bts = self.numbering.get_site_ip(self.destination)
                        self.context = 'SMS_ROAMING_INTERNAL'
                        self.send(self.source, self.destination, self.text, self.charset, current_bts)
                    else:
                        # check if number is for outbound.
                        # not implemented yet. just return
                        sms_log.info('Invalid destination for SMS')                        
                        return
        else:
            # the destination is roaming send call to current_bts
            try:
                current_bts = self.numbering.get_current_bts(self.destination)
                if current_bts == config['local_ip']:
                    sms_log.info('Destination is roaming on our site send SMS to local kannel')
                    self.context = 'SMS_ROAMING_LOCAL'
                    self.send(self.source, self.destination, self.text)
                else:
                    sms_log.info('Destination is roaming send sms to other site')
                    self.context = 'SMS_ROAMING_INTERNAL'
                    self.send(self.source, self.destination, self.text, self.charset, current_bts)
            except NumberingException as e:
                sms_log.error(e)
                

    def save(self, source, destination, context):
        # insert SMS in the history
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO sms(source_addr,destination_addr,context) VALUES(%s,%s,%s)', (source, destination, context))
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise SMSException('PG_HLR error saving SMS in the history: %s' % e)
        finally:
            cur.close()
            db_conn.commit()

    def send_immediate(self, num, text):
        appstring = 'OpenBSC'
        appport = 4242
        vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
        cmd = 'subscriber extension %s sms sender extension %s send %s' % (num, config['smsc'], text)
        vty.command(cmd)

    def broadcast_to_all_subscribers(self, text, btype):
        sub = Subscriber()
        if btype == 'all':
            subscribers_list = sub.get_all()
        elif btype == 'notpaid':
            subscribers_list = sub.get_all_notpaid()
        elif btype == 'unauthorized':
            subscribers_list = sub.get_all_unauthorized()
        elif btype == 'extension':
            subscribers_list = sub.get_all_5digits()

        for mysub in subscribers_list:
            self.send(config['smsc'], mysub[1], text)
            sms_log.debug('Broadcast message sent to %s' % mysub[1])
            time.sleep(1)

    def send_broadcast(self, text, btype):
        sms_log.info('Send broadcast SMS to all subscribers. text: %s' % text)
        t = Thread(target=self.broadcast_to_all_subscribers, args=(text, btype, ))
        t.start()

    def _t_urlopen2(self, url, data):
        try:
            res = urllib.urlopen(url, data)
            ret = res.read()
            res.close()
            try:
                j = json.loads(ret)
                sms_log.info('Status of Submitted SMS to %s: %s' % 
                    (j['messages'][0]['to'], j['messages'][0]['status']))
                sms_log.info('NEXMO Account Balance: %s' % 
                    (j['messages'][0]['remaining-balance']))
            except:
                pass
        except IOError as ex:
            sms_log.error(ex)

    def _t_urlopen(self, url, data):
        try:
            res = urllib.urlopen('http://%s:8085/sms' % url, data)
            res.read()
            res.close()
            return res
        except IOError as ex:
            sms_log.error(ex)

if __name__ == '__main__':
    sms = SMS()
    try:
        sms.send('10000', '66666248674', 'test')
        #sms.receive('68820132107','777','3010#68820135624#10','UTF-8',2)
        #sms.send_broadcasit('antani')
    except SMSException as e:
        print "Error: %s" % e
