#!/usr/bin/python
############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2017 keith <keith@rhizomatica.org>
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
'''
RCCN ESME

'''
import config
import urllib2, time
import smpplib.client
import smpplib.consts
import smpplib.exceptions
from smpplib import smpp
import gsm0338, binascii
import code
import datetime
import threading
from random import randint

smpp_messages = {}
no_unknown_delivery = 0

def cs(l, exit=0):
    code.interact(local=dict(globals(), **l))
    if exit == 1:
        exit()

def parse_udh(data):
    udh = {}
    udh['len'] = ord(data[0])
    udh['iei'] = ord(data[1])
    if udh['iei'] != smpplib.consts.SMPP_UDHIEIE_CONCATENATED:
        log.error('Unhandled IEI: %i', udh['iei'])
        return False
    udh['header_len'] = ord(data[2])
    udh['csms_ref'] = ord(data[3])
    udh['parts'] = ord(data[4])
    udh['part_num'] = ord(data[5])
    return udh

def local_submit_one(source, destination, unicode_text):
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(unicode_text)
    smpp_client = smpplib.client.Client("127.0.0.1", 2775, 90)
    smpp_client.connect()
    smpp_client.bind_transceiver(system_id="ISMPP", password="Password")
    for part in parts:
        pdu = smpp_client.send_message(
            source_addr_ton=smpplib.consts.SMPP_TON_ALNUM,
            source_addr_npi=smpplib.consts.SMPP_NPI_UNK,
            source_addr=str(source),
            dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
            dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            destination_addr=str(destination),
            data_coding=encoding_flag,
            esm_class=msg_type_flag,
            short_message=part,
            registered_delivery=False,
        )
    smpp_client.unbind()
    smpp_client.disconnect()
    del pdu
    del smpp_client

def rx_deliver_sm(pdu):
    global smpp_messages
    if not isinstance(pdu, smpplib.command.DeliverSM):
        mid = pdu.sequence
        log.debug('PDU Seq. #%s is not a DeliverSM' % pdu.sequence)
        return
    _udhi = pdu.esm_class & smpplib.consts.SMPP_GSMFEAT_UDHI
    log.info("--> RX SMS ref(%s) DataCoding (%s), TON(%s), UHDI(%s)" %
        (pdu.user_message_reference, pdu.data_coding, pdu.dest_addr_ton, _udhi))

    gsm_shift_codec = gsm0338.Codec(single_shift_decode_map=gsm0338.SINGLE_SHIFT_CHARACTER_SET_SPANISH)
    code2charset = {1:'GSM03.38', 2:'UTF-8', 4:'UTF-8', 8:'UTF-16BE'}

    _start = 0
    if _udhi:
        try:
            _udh_length = ord(pdu.short_message[:1])
            _start = _udh_length+1
            udh = parse_udh(pdu.short_message[:_udh_length+1])
            if udh is False:
                log.warning('Accept and drop message.. %s', binascii.hexlify(pdu.short_message))
                return smpplib.consts.SMPP_ESME_ROK
            '''
            if udh['part_num'] == 1:
                smpp_messages[udh['csms_ref']]=[]
            log.debug('Part %s of %s' % (udh['part_num'], udh['parts']))
            smpp_messages[udh['csms_ref']].append(pdu.short_message[_start:])
            if udh['part_num'] == udh['parts']:
                _final = ''.join(smpp_messages[udh['csms_ref']])
                smpp_messages[udh['csms_ref']] = None
                log.debug("Full SMS Message: %s" % _final.decode(code2charset[pdu.data_coding]))
                #local_submit_one('LOCAL_TEST', pdu.destination_addr, _final.decode(code2charset[pdu.data_coding]))
            '''
        except Exception as ex:
            log.debug("UDHI: Other Exception: %s", str(ex))
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            log.debug(message)
            return smpplib.consts.SMPP_ESME_RSYSERR

    try:
        log_msg = pdu.short_message[_start:].decode(code2charset[pdu.data_coding])
    except UnicodeDecodeError as ex:
        log_msg = binascii.hexlify(pdu.short_message[_start:])
        print str(ex)

    log.debug("RX SMS: [ %s ]" % log_msg)
    if int(pdu.dest_addr_ton) == smpplib.consts.SMPP_TON_INTL:
        # We cannot deliver any SMS to SMPP_TON_INTL
        #return smpplib.consts.SMPP_ESME_RSYSERR
        log.error("Unable to handle SMS for %s: SMPP_TON_INTL" % (pdu.destination_addr))
        return smpplib.consts.SMPP_ESME_RINVDSTTON
    try:
        valid_src = num.is_number_known(pdu.source_addr)
        if (not num.is_number_internal(pdu.source_addr) and
            not sub.is_authorized(pdu.source_addr, 0)):
            log.error("Unable to handle SMS from %s: Unauthorised" % (pdu.source_addr))
            return smpplib.consts.SMPP_ESME_RINVSRCADR
    except SubscriberException as ex:
        log.error("Unable to handle SMS from %s: %s" % (pdu.source_addr, ex))
        return smpplib.consts.SMPP_ESME_RINVSRCADR
    try:
        if check_extensions(pdu):
            return smpplib.consts.SMPP_ESME_ROK
    except Exception as ex:
            log.error(str(ex))
            return smpplib.consts.SMPP_ESME_RSYSERR
    if pdu.user_message_reference is None:
        log.warning("PDU has no user_message_reference.")
        pdu.user_message_reference = 0
    try:
        pdu.destination_addr = num.fivetoeleven(pdu.source_addr, pdu.destination_addr, log)
        dest_ip = num.get_current_bts(pdu.destination_addr)
    except NumberingException as ex:
        log.error("Unable to handle SMS for %s: %s" % (pdu.destination_addr, ex))
        if no_unknown_delivery == 1:
            return smpplib.consts.SMPP_ESME_RINVDSTADR
        try:
            dest_ip = num.get_site_ip_hlr(pdu.destination_addr[:6])
            if config.config['local_ip'] == dest_ip:
                return smpplib.consts.SMPP_ESME_RINVDSTADR
            log.debug('Will attempt forward to %s', dest_ip)
        except Exception as ex:
            log.error("Unable to handle SMS for %s: %s" % (pdu.destination_addr[:6], ex))
            return smpplib.consts.SMPP_ESME_RINVDSTADR

    log.debug('Registered Delivery: %s' % pdu.registered_delivery)
    log.debug('ESM Class %s' % pdu.esm_class)
    if int(pdu.esm_class) == 4:
        pdu.esm_class = 8
        log.info('--> RX Delivery Report for Uref(%s): %s ' %
                  (pdu.user_message_reference, pdu.short_message))
        pdu.short_message = ' '
    if config.config['local_ip'] == dest_ip:
        ret = local_pass_pdu(pdu)
        if pdu.esm_class != 8:
            sms.save(pdu.source_addr, pdu.destination_addr, 'SMS_LOCAL')
        return smpplib.consts.SMPP_ESME_ROK
    if (hasattr(config, 'sip_central_ip_address') and
            isinstance(config.sip_central_ip_address, list) and
            config.sip_central_ip_address[0] == dest_ip):
        log.info('--> RX SMS for Webphone(%s): %s ' %
                  (pdu.user_message_reference, pdu.short_message))
        if sms.webphone_sms(pdu.source_addr, pdu.destination_addr, pdu.short_message, pdu.data_coding):
            return smpplib.consts.SMPP_ESME_ROK
        else:
            return smpplib.consts.SMPP_ESME_RSYSERR
    else:
        # Pass it off to the Queue. what to do here? send it to the remote site?
        # via rapi?
        # Should we decode the entire message?
        # what if the remote site is down
        try:
            #tremote = threading.Thread(target=remote_pass_pdu)
            stat = remote_pass_pdu(pdu, dest_ip)
            if stat == smpplib.consts.SMPP_ESME_ROK and pdu.esm_class != 8:
                sms.save(pdu.source_addr, pdu.destination_addr, 'SMS_INTERNAL')
            return stat
        except Exception as e:
            log.error("exception from remote_pass_pdu %s", str(e))
            # Something bad happened
            return smpplib.consts.SMPP_ESME_RSYSERR

def check_extensions(pdu):
        if not pdu.destination_addr in config.extensions_list:
            return False
        log.info('Destination number is a shortcode, execute shortcode handler')
        extension = config.importlib.import_module('extensions.ext_'+pdu.destination_addr, 'extensions')
        try:
            log.debug('Exec shortcode handler')
            extension.handler('', pdu.source_addr, pdu.destination_addr, pdu.short_message)
            return True
        except config.ExtensionException as e:
            raise Exception('Receive SMS error: %s' % e)

def remote_pass_pdu(pdu, dest_ip):

    try:
        log.info('Making SMMP Connection to %s for %s' % (dest_ip, pdu.destination_addr))
        smpp_client = smpplib.client.Client(dest_ip, 2775, 5)
        smpp_client.set_message_sent_handler(lambda pdu: log.info("Sent (%s)", pdu.message_id))
        smpp_client.connect()
        smpp_client.bind_transceiver(system_id="ISMPP", password="Password")
        log.debug('Submitting to %s from %s' % (pdu.destination_addr, pdu.source_addr))
        #rand = randint(5, 15)
        #log.debug('GOING BUSY NOW for %s secs' % rand)
        #time.sleep(rand)
        rpdu = smpp.make_pdu('submit_sm', client=smpp_client,
                             service_type=pdu.service_type,
                             sequence=pdu.sequence,
                             source_addr_ton=int(pdu.source_addr_ton),
                             source_addr_npi=int(pdu.source_addr_npi),
                             source_addr=pdu.source_addr,
                             dest_addr_ton=int(pdu.dest_addr_ton),
                             dest_addr_npi=int(pdu.dest_addr_npi),
                             destination_addr=pdu.destination_addr,
                             data_coding=int(pdu.data_coding),
                             esm_class=int(pdu.esm_class),
                             short_message=pdu.short_message,
                             registered_delivery=int(pdu.registered_delivery),
                             user_message_reference=int(pdu.user_message_reference)
                            )
        rpdu.sequence = pdu.sequence
        try:
            smpp_client.send_pdu(rpdu)
            log.debug('Sumbit_SM is sent. waiting response...')
            smpp_client.read_once()
            return smpplib.consts.SMPP_ESME_ROK
        except smpplib.exceptions.PDUError as ex:
            smpp_client.unbind()
            smpp_client.disconnect()
            raise Exception('Unable to Submit Message via Remote SMPP (%s)' % ex)
        smpp_client.unbind()
        smpp_client.disconnect()
        del smpp_client
        if p.sequence == rpdu.sequence:
            log.debug('Remote SMPP Resp Received for Sequence# %s' % pdu.sequence)
            return smpplib.consts.SMPP_ESME_ROK
    except (IOError, smpplib.exceptions.ConnectionError) as ex:
        smpp_client.disconnect()
        raise Exception('Unable to connect to Remote SMPP (%s)' % ex)
    except Exception as ex:
        log.debug("Other Exception: %s", str(ex))
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        log.debug(message)
        del smpp_client
        raise Exception(ex)

def local_pass_pdu(pdu):

    if pdu.user_message_reference is None:
        pdu.user_message_reference = 0
    return client.send_message(
        service_type=pdu.service_type,
        source_addr_ton=int(pdu.source_addr_ton),
        source_addr_npi=int(pdu.source_addr_npi),
        source_addr=pdu.source_addr,
        dest_addr_ton=int(pdu.dest_addr_ton),
        dest_addr_npi=int(pdu.dest_addr_npi),
        destination_addr=pdu.destination_addr,
        data_coding=int(pdu.data_coding),
        esm_class=int(pdu.esm_class),
        short_message=pdu.short_message,
        registered_delivery=int(pdu.registered_delivery),
        user_message_reference=int(pdu.user_message_reference)
    )

def post_tx_message(pdu):
    log.info('Local SMSC msgid(%s) sequence(%s)' % (pdu.message_id, pdu._sequence))
    return
    #cs(locals())
    dlr = smpplib.smpp.make_pdu('submit_sm',
                                source_addr_ton=pdu.dest_addr_ton,
                                source_addr=pdu.dest_addr,
                                dest_addr_ton=pdu.source_addr_ton,
                                destination_addr=pdu.source_addr,
                                short_message='',
                                esm_class=0x08,
                                user_message_reference=pdu.user_message_reference
                               )
    client.send_pdu(dlr)

def smpp_bind(client):
    while True:
        try:
            smpplib.client.logger.setLevel('INFO')
            client.set_message_received_handler(rx_deliver_sm)
            client.set_message_sent_handler(post_tx_message)
            #client.set_test_handler(my_test)
            #client.disconnect()
            client.connect()
            # Bind to OSMPP, out configured default-route in nitb.
            client.bind_transceiver(system_id="OSMPP", password="Password")
            #client.test_handler(client, foo="bar")
            log.info('Listening....')
            client.listen([11])
        except smpplib.exceptions.ConnectionError as e:
            print ("Connection Error (%s)" % e)
            client.disconnect()
            time.sleep(1)

if __name__ == "__main__":
    re = config.re
    sys = config.sys
    riak_client = config.riak_client
    myprefix = config.config['internal_prefix']
    myip = config.config['local_ip']
    log = config.sms_log
    log.setLevel(config.default_log_level)
    sub = config.Subscriber()
    SubscriberException = config.subscriber.SubscriberException
    num = config.Numbering()
    NumberingException = config.numbering.NumberingException
    sms = config.SMS()
    SMSException = config.sms.SMSException
    log.info('Starting up ESME...')
    # host, port, timeout, sequence_generator
    client = smpplib.client.Client("127.0.0.1", 2775, 90)
    smpp_bind(client)
