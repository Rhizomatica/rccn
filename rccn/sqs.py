#!/usr/bin/env python
############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2018 keith <keith@rhizomatica.org>
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
"""
Rhizomatica SMS Queue Sync
"""

from optparse import OptionParser
from datetime import datetime
from dateutil import tz
import code
import OsmoSmsQ
import smpplib
import smpplib.gsm
import config as cn

parser = OptionParser()
parser.add_option("-n", "--noop", dest="noop", action="store_true",
                  help="NO OP. Don't do anything")
parser.add_option("-r", "--rccn", dest="rccn", action="store_true",
                  help="Use RCCN routine to submit messages instead of SMPP (dangerous)")
parser.add_option("-f", "--full", dest="full", action="store_true",
                  help="Display full message text")
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Show Debug Output (otherwise fairly quiet)")

(options, args) = parser.parse_args()

OsmoSmsQ.sms_db = cn.sms_db
OsmoSmsQ.log = cn.sms_log
sms_log = cn.sms_log
numbering = cn.Numbering()
subs = cn.Subscriber()
sms = cn.SMS()

if options.debug:
    sms_log.setLevel('DEBUG')

def smpp_sumbit(src, dest, utext, bts, report=False):
    global _sent

    def _smpp_rx_submit_resp(pdu):
        global _sent
        sms_log.info("Sent (%s)", pdu.message_id)
        if pdu.command == "submit_sm_resp":
            _sent = pdu.status

    try:
        parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(utext)
        smpp_client = smpplib.client.Client(bts, 2775, 90)
        smpplib.client.logger.setLevel('INFO')
        smpp_client.set_message_received_handler(lambda pdu: sms_log.info("Rcvd while sending (%s)", pdu.command))
        smpp_client.set_message_sent_handler(_smpp_rx_submit_resp)
        smpp_client.connect()
        smpp_client.bind_transmitter(system_id="ISMPP", password="Password")
        _sent = -1
        for part in parts:
            pdu = smpp_client.send_message(
                source_addr_ton=smpplib.consts.SMPP_TON_ALNUM,
                source_addr_npi=smpplib.consts.SMPP_NPI_UNK,
                source_addr=str(src),
                dest_addr_ton=smpplib.consts.SMPP_TON_SBSCR,
                dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
                destination_addr=str(dest),
                data_coding=encoding_flag,
                esm_class=msg_type_flag,
                short_message=part,
                registered_delivery=report,
            )
            while _sent < 0:
                smpp_client.read_once()
        smpp_client.unbind()
        smpp_client.disconnect()
        del pdu
        del smpp_client
        return 0
    except (IOError, smpplib.exceptions.ConnectionError, smpplib.exceptions.PDUError) as ex:
        if isinstance(ex, smpplib.exceptions.PDUError):
            smpp_client.unbind()
            smpp_client.disconnect()
            sms_log.info('Remote said %s', str(ex))
            return ex.args[1]
        raise cn.SMSException('Unable to Submit Message via SMPP: (%s)', str(ex))

def rccn_submit(src, dest, utext, bts):
    try:
        sms_log.info("Re-Injecting for %s [%s]...." % (c_bts, utext.encode('utf-8', 'replace')))
        result = sms.send(src, dest, utext, 'unicode', c_bts)
        sms_log.debug("Result from SMS.send(): %s", result)
        return result
    except Exception as ex:
        raise cn.SMSException("Exception [ %s ] while reinjecting Message" % ex)

def mark_local(mid):
    # NOTE: In RCCN mode, There's no way to know for sure if the remote actually got the message,
    # In fact, the remote RAPI thread will drop it on failure, but we've already returned :/
    smsc_db_conn = cn.sqlite3.connect(cn.sms_db, timeout=5)
    smsc_db_cursor = smsc_db_conn.cursor()
    for i in mid.split(','):
        sms_log.debug("UPDATE SMS SET valid_until=9990999, sent=CURRENT_TIMESTAMP WHERE id=%s" % i)
        smsc_db_cursor.execute("UPDATE SMS SET valid_until=9990999,sent=CURRENT_TIMESTAMP WHERE id=?", [(i)])
    smsc_db_conn.commit()
    smsc_db_conn.close()

try:
    # read_queue(q_id = 0, unsent = False, sent = False, where = '', src = '', dest = '', both = '', negate = False)
    try:
        connected = subs.get_all_connected()
    except:
        connected = []
        pass
    sub = subs.get_all_expire()
    expire_lu = {el[0]:el[1] for el in sub}
    lev = sms_log.level
    sms_log.setLevel(cn.logging.INFO)
    smsq = OsmoSmsQ.read_queue(0, True, False, '', '10000', '', '', True)
    msgs = OsmoSmsQ.build_msgs(smsq)
    sms_log.setLevel(lev)
    n = 0
    sent = 0
    not_here = 0
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    today = datetime.today().replace(tzinfo=to_zone)
    for item in msgs:
        s = item['sms']
        mid = item['mid']
        utext = item['text']
        src = item['src']
        dest = item['dest']
        coding = item['coding']
        reg_delivery = item['reg_delivery']
        created = datetime.strptime(item['created'], '%Y-%m-%d %X').replace(tzinfo=from_zone).astimezone(to_zone)
        days = (today-created).days
        n = n + 1
        if len(dest) < 11 or not unicode(dest).isnumeric():
            sms_log.debug("[%s] Skipping Destination: %s from %s" % (mid, dest, src))
            continue
        mark = '92' if cn.config['internal_prefix'] == dest[:6] else '91'
        display = utext if options.full else utext[:15]
        sms_log.debug("\033[98;1m(%s day)\033[0m old Message ID: %s for \033[%s;3m%s\033[0m [ \033[93m%s\033[0m ]" %
                      (days, mid, mark, dest, display))
        try:
            c_bts = numbering.get_current_bts(dest)
        except cn.NumberingException as ex:
            sms_log.debug(ex)
            c_bts = numbering.get_site_ip_hlr(dest[:6])
            #continue
            #pass

        try:
            last = datetime.strptime(expire_lu[dest], '%Y-%m-%d %X').replace(tzinfo=from_zone).astimezone(to_zone).strftime("%Y-%m-%d %H:%M:%S")
        except KeyError:
            last = 'UNKNOWN!'
            if cn.config['internal_prefix'] != dest[:6]:
                try:
                    bts = numbering.get_site_ip_hlr(dest[:6])
                    sms_log.debug('-----> This SMS is for a purged roaming user! Try to send it home (%s).', bts)
                    if not options.noop:
                        if options.rccn:
                            resp = rccn_submit(src, dest, utext, c_bts)
                            mark_local(mid)
                        if not options.rccn:
                            sm_resp = smpp_sumbit(src, dest, utext, bts, reg_delivery)
                            if sm_resp == 0:
                                sent = sent + 1
                                mark_local(mid)
                except (cn.SMSException, cn.NumberingException) as ex:
                    sms_log.error(str(ex))
            continue

        if c_bts != cn.vpn_ip_address:

            sms_log.debug("-----> (\033[%s;3m%s\033[0m) is at %s according to HLR. LU Expired: (\033[92;1m%s\033[94;1m%s\033[0m)" %
                          (mark, dest, c_bts, last[:10], last[10:]))
            not_here = not_here + 1

            if options.noop:
                continue
            try:
                if options.rccn:
                    resp = rccn_submit(src, dest, utext, c_bts)
                if not options.rccn:
                    sm_resp = smpp_sumbit(src, dest, utext, c_bts, reg_delivery)
                    if sm_resp != 0:
                        continue
            except cn.SMSException as ex:
                sms_log.error(str(ex))
                continue
            else:
                sms_log.info("Got no Exception, going to mark message locally as sent")
                sent = sent + 1
                mark_local(mid)
        else:
            sms_log.debug("(\033[%s;3m%s\033[0m) is here according to HLR. LU Expired: (\033[92;1m%s\033[94;1m%s\033[0m)" %
                          (mark, dest, last[:10], last[10:]))
            if dest in connected:
                sms_log.debug("Destination Number (%s) even appears to be connected!", dest)
    sms_log.info("Queue Sender looked at %s messages in the Queue. %s not here. Sent: %s", n, not_here, sent)

except Exception as ex:
    print "Top Level Exception"
    print ex
    #code.interact(local=locals())
