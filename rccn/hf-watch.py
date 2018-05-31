#!/usr/bin/python
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
'''
rhizo-hf-connector folder watch

'''

import os, re
import inotify.adapters
import config
import ESL

if __name__ == "__main__":
    sms = config.SMS()
    log=config.log

    if config.hermes == 'central':
        direction = 'outgoing'
        _hermes_path = b'/var/spool/' + direction + '_messages/'
    if config.hermes == 'remote':
        direction = 'incoming'
        _hermes_path = b'/var/spool/' + direction + '_messages/'
    try:
        if not os.path.exists(_hermes_path):
            os.makedirs(_hermes_path)
    except Exception as e:
        log.debug(e)
        exit(-1)

    log.info('Starting up RHIZ0-HF-WATCH for HERMES-%s' % config.hermes)

    i = inotify.adapters.Inotify()
    i.add_watch(_hermes_path)

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                log.debug("Watcher event for file: %s %s" % (filename, type_names))
                if 'IN_CLOSE_WRITE' == type_names[0]:
                    _full_path = _hermes_path+filename
                    log.info("File: %s was written." % (_full_path))
                    if not os.path.isfile(_full_path):
                        log.info("File: %s was deleted!" % (_full_path))
                        continue
                    m = re.match('(msg|call)-(.*).(txt|gsm)', filename)
                    if not m:
                        log.info("File: %s not of interest to us." % (_full_path))
                        continue
                    #import code
                    #code.interact(local=locals())
                    
                    if m.groups()[0] == 'msg':
                        _seq = m.groups()[1]
                        with open(_full_path, "r") as file:
                            _source = file.readline().strip()
                            _dest = file.readline().strip()
                            _msg = ''
                            _line = file.readline()
                            while _line:
                                _msg = _msg + _line.strip()
                                _line = file.readline()
                        log.info("Message (%s) from: %s to %s with %s" % (_seq, _source, _dest, _msg) )
                        if config.hermes == 'remote':
                            # Deliver this SMS to the local SMSC (via rapi)
                            sms.receive(_source, _dest, _msg, 'utf-8', 0, _seq)
                        if config.hermes == 'central':
                            # Deliver this SMS to the upstream provider.
                            sms.route_intl_service(_source, _dest, _msg, _seq)
                    if m.groups()[0] == 'call':
                        _seq = m.groups()[1].split('-')[0]
                        _caller = m.groups()[1].split('-')[1]
                        _callee = m.groups()[1].split('-')[2]
                        log.info('New audio message found from %s to %s' % (_caller, _callee))
                        # FIXME: I think what is needed here is to send the B leg into a dialplan
                        # where we can control what happens and then interact with the callee.
                        try:
                            con = ESL.ESLconnection("127.0.0.1", "8021", "ClueCon")
                            if config.hermes == 'central':
                                # Our Message needs to go upstream to VOIP
                                _callee = '+'+_callee
                                sip_route = "gateway/rhizomatica"
                                sip_dest = ""
                            if config.hermes == 'remote':
                                # Our Message is being sent to the local GSM Net.
                                # FIXME, Make this lookup properly in the database.
                                sip_route = 'internal'
                                sip_dest = "@"+config.mncc_ip_address+":5050"
                                #sip_dest = "@192.168.11.121:5061"
                            _sofia_str = (
                                "{orig_uuid="+_seq+"}"
                                "sofia/"+sip_route+"/"+str(_callee)+sip_dest+" "
                                ""+_caller+" XML hermes +"+_caller +" +"+_caller+""
                                )
                            log.info('FS originate: %s' % _sofia_str)
                            e = con.api("originate", _sofia_str)
                            if e:
                                res = e.getBody()
                                log.info("Freeswitch Response: %s" % res)
                                if res[:3] != "+OK":
                                    log.info("Call did not go through, what to do?")
                        except Exception as ex:
                            print str(ex)

                        # Call ?

                log.debug("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                             "WATCH-PATH=[%s] FILENAME=[%s]",
                             header.wd, header.mask, header.cookie, header.len, type_names,
                             watch_path.decode('utf-8'), filename.decode('utf-8'))

    except Exception as e:
        log.info(e)
    

