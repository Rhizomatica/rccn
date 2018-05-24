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
import obscvty, urllib2, time
import smpplib.client
import smpplib.consts
import smpplib.exceptions
from smpplib import smpp
import gsm0338
import code
import datetime
import threading
from random import randint
from binascii import hexlify


def cs(l, exit = 0):
    code.interact(local = dict(globals(), **l) )
    if exit == 1:
      exit()

def route_to_hfconnector(src,dest,msg,seq):
    _hermes_path = '/var/spool/outgoing_messages/'
    try:
        _sms_file = _hermes_path + "Outgoing_SMS_" + str(seq) + '.txt'
        with open(_sms_file, "w") as file:
            file.write("{0}\n".format(str(src)))
            file.write("{0}\n".format(str(dest)))
            file.write("{0}\n".format(str(msg)))
        log.debug('Wrote SMS to %s' % _sms_file)
        return 0
    except Exception as e:
        log.debug(e)
        return -1

def check_for_shortcode(pdu):
    if pdu.destination_addr == '111':
        _svc = 'HELP'
        _help_str = (
        "Text to 111 for HELP\n"
        "Text to 222 to Update your Name.\n"
        "Text to 555 to Search.\n")
        if len(_help_str) < 160:
            local_submit(_svc,str(pdu.source_addr),_help_str)
        else:
            return -1;
        return True

    if pdu.destination_addr == '555':
        _svc = '555'
        search = pdu.short_message
        if pdu.data_coding == 8:
            search = ""
        _results = sub.get_all_by_name(search)
        if len(_results) == 0:
            local_submit(_svc,str(pdu.source_addr),"No results for "+str(pdu.short_message))
            return True
        _results_str = "Results for "+str(pdu.short_message)+":\n"
        for entry in _results:
            _results_str = _results_str + entry[2]+': '+entry[1]+'\n';
        log.info("Search Results: %s" % _results_str)
        if len(_results_str) < 160:
            local_submit(_svc,str(pdu.source_addr),_results_str)
        else:
            local_submit(_svc,str(pdu.source_addr),"Too many Results\n")
        return True
    if pdu.destination_addr == '222':
        _svc = '222'
        _name = ''.join(i for i in pdu.short_message if ord(i)>31 and ord(i)<127)
        try:
            sub.edit(pdu.source_addr,_name,'','','','')
        except SubscriberException as e:
            local_submit(_svc,str(pdu.source_addr),str(e))
            return -1
        local_submit(_svc,str(pdu.source_addr),'Name updated to '+_name)
        return True
    return -1

def local_report(pdu):

    return client.send_message(
        source_addr_ton = int(pdu.dest_addr_ton),
        source_addr_npi= int(pdu.dest_addr_npi),
        source_addr = str(pdu.destination_addr),
        dest_addr_ton = int(pdu.source_addr_ton),
        dest_addr_npi = int(pdu.source_addr_npi),
        destination_addr = str(pdu.source_addr),
        data_coding = int(pdu.data_coding),
        esm_class = 0x08,
        user_message_reference = int(pdu.user_message_reference),
        short_message = 'Delivery Report'
    )

def rx_deliver_sm(pdu):
    if not isinstance(pdu, smpplib.command.DeliverSM):
        mid = pdu.sequence
        log.debug('PDU Seq. #%s is not a DeliverSM' % pdu.sequence)
        if isinstance(pdu, smpplib.command.AlertNotification):
            log.debug('Alert: %s %s' % (pdu.source_addr, pdu.ms_availability_status))
        return
    log.debug("Data Coding: %s" % pdu.data_coding)
    if int(pdu.data_coding) == 8:
        #cs(locals())
        log_msg = hexlify(pdu.short_message)
    elif int(pdu.data_coding) == 4:
        log_msg = pdu.short_message.decode('utf8')
    else:
        gsm_shift_codec = gsm0338.Codec(single_shift_decode_map=gsm0338.SINGLE_SHIFT_CHARACTER_SET_SPANISH)
        log_msg=gsm_shift_codec.decode(pdu.short_message)[0]
    log.info("RX SMS: \n==========\n%s\n==========\n" % log_msg)
    log.debug("RX SMS with TON: %s" % pdu.dest_addr_ton)
    if check_for_shortcode(pdu) == True:
        local_report(pdu)
        return smpplib.consts.SMPP_ESME_ROK

    if int(pdu.dest_addr_ton) == smpplib.consts.SMPP_TON_INTL:
        # FIXME Deal properly with multipart messages.
        rc = -1
        if config.sms_route_intl_hermes == 'yes':
            rc = route_to_hfconnector(pdu.source_addr,pdu.destination_addr,
                                pdu.short_message,pdu.sequence)
        if config.sms_route_intl_service == 'yes':
            rc = sms.route_intl_service(pdu.source_addr,pdu.destination_addr,
                                pdu.short_message,pdu.sequence)
        if rc == 0:
                return smpplib.consts.SMPP_ESME_ROK

        # We cannot deliver any SMS to SMPP_TON_INTL
        log.info("Unable to handle SMS for %s: SMPP_TON_INTL" % (pdu.destination_addr) )
        return smpplib.consts.SMPP_ESME_RINVDSTADR
        #return smpplib.consts.SMPP_ESME_RSYSERR
        #return smpplib.consts.SMPP_ESME_RINVSRCADR

    try:
        valid_src = sub.get(pdu.source_addr)
        if not sub.is_authorized(pdu.source_addr,0):
            log.info("Unable to handle SMS from %s: Unauthorised" % (pdu.source_addr) )
            return smpplib.consts.SMPP_ESME_RINVSRCADR
        if not sub.is_authorized(num.fivetoeleven(pdu.source_addr,pdu.destination_addr), 0):
            log.info("Unable to handle SMS to %s: Unauthorised" % (pdu.destination_addr) )
            return smpplib.consts.SMPP_ESME_RINVDSTADR
    except SubscriberException as ex:
        log.info("Unable to handle SMS from %s: %s" % (pdu.source_addr,ex) )
        return smpplib.consts.SMPP_ESME_RINVSRCADR
    try:
        pdu.destination_addr = num.fivetoeleven(pdu.source_addr,pdu.destination_addr)
        dest_ip = num.get_current_bts(pdu.destination_addr)
    except NumberingException as ex:
        log.info("Unable to handle SMS for %s: %s" % (pdu.destination_addr,ex) )
        return smpplib.consts.SMPP_ESME_RINVDSTADR

    #log.info("SMS from %s to %s" % (valid_src[2], valid_dest[2]) )

    log.debug('Registered Delivery: %s' % pdu.registered_delivery) 
    log.debug('ESM Class %s' % pdu.esm_class) 
    if int(pdu.esm_class) == 4:
        pdu.esm_class = 8
        log.debug('Delivery Report for msg_ref: %s %s ' % 
            (pdu.user_message_reference, '') )
    if config.config['local_ip'] == dest_ip:
        ret = local_pass_pdu(pdu)
        return smpplib.consts.SMPP_ESME_ROK
    else:
        # Pass it off to the Queue. what to do here? send it to the remote site?
        # via rapi? 
        # Should we decode the entire message?
        # what if the remote site is down
        try:
            tremote = threading.Thread(target=remote_pass_pdu)
            return remote_pass_pdu(pdu,dest_ip)
        except Exception as e:
            log.info(e)
            # Something bad happened
            return smpplib.consts.SMPP_ESME_RSYSERR
            

def remote_pass_pdu(pdu,dest_ip):

    try:
        log.debug('Making SMMP Connection to %s for %s' % (dest_ip, pdu.destination_addr) )
        smpp_client = smpplib.client.Client(dest_ip, 2775, 5)
        smpp_client.connect()
        smpp_client.bind_transceiver(system_id="ISMPP", password="Password")
        log.debug('Submitting %s' % pdu.short_message)
        rand=randint(5,15)
        #log.debug('GOING BUSY NOW for %s secs' % rand)
        #time.sleep(rand)
        rpdu = smpp.make_pdu('submit_sm', client=smpp_client,
            sequence = pdu.sequence,
            source_addr_ton = int(pdu.source_addr_ton),
            source_addr_npi= int(pdu.source_addr_npi),
            source_addr = pdu.source_addr,
            dest_addr_ton = int(pdu.dest_addr_ton),
            dest_addr_npi = int(pdu.dest_addr_npi),
            destination_addr = pdu.destination_addr,
            data_coding = int(pdu.data_coding),
            esm_class = int(pdu.esm_class),
            short_message = pdu.short_message,
            registered_delivery = int(pdu.registered_delivery),
            user_message_reference = int(pdu.user_message_reference)
        )        
        rpdu.sequence = pdu.sequence
        try:
            smpp_client.send_pdu(rpdu)
        except smpplib.exceptions.PDUError:
            smpp_client.unbind()
            smpp_client.disconnect()
            raise Exception('Unable to Submit Message via Remote SMPP %s' % e)
        log.debug('Sumbit_SM is sent. waiting..')
        time.sleep(1)
        p=smpp_client.read_pdu()
        log.debug("Remote SMSC Message ID: %s" % p.message_id)
        #code.interact(local=locals())
        smpp_client.unbind()
        smpp_client.disconnect()
        del smpp_client
        if (p.sequence == rpdu.sequence):
            log.debug('Remote SMPP Resp Received for Sequence# %s' % pdu.sequence)
            return smpplib.consts.SMPP_ESME_ROK
    except (IOError, smpplib.exceptions.PDUError) as e:
        raise Exception('Unable to Submit Message via Remote SMPP %s' % e)
    except Exception as e:
        print "Other Exception: " + str(e)
        raise Exception(e)
    
def local_pass_pdu(pdu):

    return client.send_message(
        source_addr_ton = int(pdu.source_addr_ton),
        source_addr_npi= int(pdu.source_addr_npi),
        source_addr = pdu.source_addr,
        dest_addr_ton = int(pdu.dest_addr_ton),
        dest_addr_npi = int(pdu.dest_addr_npi),
        destination_addr = pdu.destination_addr,
        data_coding = int(pdu.data_coding),
        esm_class = int(pdu.esm_class),
        short_message = pdu.short_message,
        registered_delivery = int(pdu.registered_delivery),
        user_message_reference = int(pdu.user_message_reference)
    )

def local_submit(src,dst,message):

    return client.send_message(
        source_addr_ton=smpplib.consts.SMPP_TON_ALNUM,
        source_addr_npi=smpplib.consts.SMPP_NPI_UNK,
        source_addr=src,
        dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
        dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
        destination_addr=dst,
        short_message=message,
        data_coding=smpplib.consts.SMPP_ENCODING_DEFAULT,
        esm_class= 2, # smpplib.consts.SMPP_MSGTYPE_DEFAULT,
        registered_delivery=0,
        user_message_reference = 0xFF
        )

def post_tx_message(pdu):
    log.debug('SMSC said msgid: %s, sequence: %s' % (pdu.message_id, pdu._sequence))
    return;
    #cs(locals())
    dlr = smpplib.smpp.make_pdu('submit_sm',
        source_addr_ton = pdu.dest_addr_ton,
        source_addr = pdu.dest_addr,
        dest_addr_ton = pdu.source_addr_ton,
        destination_addr = pdu.source_addr,
        short_message = '',
        esm_class = 0x08,
        user_message_reference = pdu.user_message_reference
    )
    client.send_pdu(dlr)

def smpp_bind(client):
    while True:
        try:
            smpplib.client.logger.setLevel('DEBUG')
            client.set_message_received_handler(rx_deliver_sm)
            client.set_message_sent_handler(post_tx_message)
            #client.set_test_handler(my_test)
            client.disconnect()
            client.connect()
            # Bind to OSMPP, out configured default-route in nitb.
            client.bind_transceiver(system_id="OSMPP", password="Password")
            #client.test_handler(client, foo="bar")
            client.listen([11])
        except smpplib.exceptions.ConnectionError as e:
            print e
            time.sleep(1)            

if __name__ == "__main__":
    re=config.re
    sys=config.sys
    riak_client=config.riak_client
    myprefix=config.config['internal_prefix']
    myip=config.config['local_ip']
    log=config.log
    sub=config.Subscriber()
    SubscriberException = config.subscriber.SubscriberException
    num=config.Numbering()
    NumberingException = config.numbering.NumberingException
    sms=config.SMS()
    SMSException = config.sms.SMSException
    #open a VTY console, don't bring up and down all the time.
    #vty = obscvty.VTYInteract('OpenBSC', '127.0.0.1', 4242)
    log.info('Starting up ESME')
    # host, port, timeout, sequence_generator
    client = smpplib.client.Client("127.0.0.1", 2775, 90)
    smpp_bind(client)
