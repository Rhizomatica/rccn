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
SMPP Listener for Alert Notificaions
Reacts in real time to do best effort update of the d_hlr, taking into consideration
we might be disconnected from the world at the time of the notification.

Very much a POC, in prototype mode at this time. Once this is established stuff should be moved
to classes, possibly existing classes within RCCN

'''
import config
import obscvty, urllib2, time
import smpplib.client
import smpplib.consts

def _get_imsi(ext):
    try:
        cmd = 'show subscriber extension %s' % (ext)
        ret = vty.command(cmd)
        m = re.compile('IMSI: ([0-9]*)').search(ret)
        if m:
            return m.group(1)
        else:
            return False
    except:
        print sys.exc_info()[1]
        return False

def rx_alert_notification(pdu):

    #print pdu.source_addr_ton, pdu.source_addr_npi, pdu.source_addr, pdu.ms_availability_status
    # Sanity check that we got imsi/extension
    if pdu.source_addr_ton == 3 and pdu.source_addr_npi == 1:
        mode = 'EXT'
    elif pdu.source_addr_ton == 4 and pdu.source_addr_npi == 6:
        mode = 'IMSI'
    else:
        return

    if pdu.ms_availability_status == 2:
        log.info('Received Detach Notification for %s: %s' % (mode, pdu.source_addr))
        if mode == 'EXT':
            extension = pdu.source_addr
            if len(extension) == 5: # Ignore these.
                return
            if extension[:6] != myprefix:
                log.info('Detach from foreign extension, send it home.')
                imsi = _get_imsi(extension)
                try:
                    rk_hlr = riak_client.bucket('hlr')
                    subscriber = rk_hlr.get(str(imsi), timeout=config.RIAK_TIMEOUT)
                    log.info('RIAK: pushing %s, was %s' % (subscriber.data['home_bts'], subscriber.data['current_bts']))
                    subscriber.data['current_bts'] = subscriber.data['home_bts']
                    now = int(time.time())
                    subscriber.data['updated'] = now
                    subscriber.indexes = set([('modified_int', now), ('msisdn_bin', subscriber.data['msisdn'])])
                    subscriber.store()
                    sub._update_location_pghlr(subscriber)
                except Exception as e:
                    print str(e)
                sub.update_location_local_hlr(extension)
                log.info('Tell home about it..')
                if subscriber.data['current_bts']:
                    current_bts = subscriber.data['current_bts']
                    try:
                        values = '{"msisdn": "%s", "local": "yes" }' % extension
                        opener = urllib2.build_opener(urllib2.HTTPHandler)
                        request = urllib2.Request('http://%s:8085/subscriber/offline' % current_bts, data=values)
                        request.add_header('Content-Type', 'application/json')
                        request.get_method = lambda: 'PUT'
                        res = opener.open(request).read()
                        if 'success' in res:
                            log.info('Roaming Subscriber %s returned to %s' % (extension, current_bts))
                        else:
                            log.error('Error (%s) Returning Roaming Subscriber %s at %s' %
                                      (config.json.loads(res)['error'], extension, current_bts))
                    except IOError:
                        log.error('Error connect to site %s to return subscriber %s' % (current_bts, extension))

    if pdu.ms_availability_status == 0:
        log.info('Received LUR/Attach Notification for %s: %s' % (mode, pdu.source_addr))
        if mode == 'EXT':
            extension = pdu.source_addr
            if len(extension) == 5:
                # Ignore 5 digit extensions for the moment, let the RRC task bring them up.
                # I'd like to react to them, but need the full hlr db with IMSIs
                # locally at least.
                return
            try:
                current_bts = num.get_current_bts(extension)
            except config.NumberingException as ex:
                log.debug('!! No subscriber in hlr?? %s', str(ex))
                return
            if current_bts != myip:
                # Our HLR doesn't expect this MS to be here.
                # So either the hlr is out of date, or this is new here.
                imsi = _get_imsi(pdu.source_addr)
                try:
                    sub.update_location(imsi, extension, True)
                except config.SubscriberException as ex:
                    log.debug('Subscriber error: %s', str(ex))
                    return

                # a riak exception in the previous
                # function would prevent the local PG update.
                # this is usually overkill, to be sure, to be sure...
                sub.update_location_local_hlr(extension, myip)

                # Expire this on where I think it was last.
                try:
                    values = '{"msisdn": "%s"}' % extension
                    opener = urllib2.build_opener(urllib2.HTTPHandler)
                    request = urllib2.Request('http://%s:8085/subscriber/offline' % current_bts, data=values)
                    request.add_header('Content-Type', 'application/json')
                    request.get_method = lambda: 'PUT'
                    res = opener.open(request).read()
                    if 'success' in res:
                        log.info('Roaming Subscriber %s expired on %s' % (extension, current_bts))
                    else:
                        log.error('Error (%s) Expiring Roaming Subscriber %s at %s' %
                                  (config.json.loads(res)['error'], extension, current_bts))
                except IOError:
                    log.error('Error connecting to site %s to expire subscriber %s' % (current_bts, extension))

        else:
            # Mode deliver-src-imsi (not used)
            extension = sub.get_local_extension(pdu.source_addr)
            if extension[:6] == myprefix:
                print "That's mine"
                bts = num.get_local_hlr_btsinfo(extension)
                print "My HLR says %s" % bts['current_bts']
            else:
                try:
                    bts = num.get_local_hlr_btsinfo(extension)
                except config.NumberingException as ne:
                    print str(ne)
                    return

            print "That is from %s last seen %s" % (bts['home_bts'], bts['current_bts'])

def smpp_bind():
    client = smpplib.client.Client("127.0.0.1", 2775, 90)
    client.set_message_received_handler(rx_alert_notification)
    client.connect()
    client.bind_transceiver(system_id="NOTIFY", password="Password")
    client.listen()

if __name__ == "__main__":
    re = config.re
    sys = config.sys
    riak_client = config.riak_client
    myprefix = config.config['internal_prefix']
    myip = config.config['local_ip']
    log = config.roaming_log
    sub = config.Subscriber()
    num = config.Numbering()
    #open a VTY console, don't bring up and down all the time.
    vty = obscvty.VTYInteract('OpenBSC', '127.0.0.1', 4242)
    log.info('Starting up alert notification listener for %s on %s' % (myprefix, myip))
    smpp_bind()
