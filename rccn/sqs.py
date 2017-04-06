#!/usr/bin/env python
############################################################################
#
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
"""
Rhizomatica SMS Queue Sync
"""

from config import *
import code
import OsmoSmsQ
OsmoSmsQ.sq_hlr_path=sq_hlr_path
OsmoSmsQ.log=sms_log
numbering = Numbering()
sms = SMS()

#code.interact(local=dict(globals(), **locals()))

try:
    # read_queue(q_id = 0, unsent = False, sent = False, where = '', src = '', dest = '', negate = False)
    lev = sms_log.level
    sms_log.setLevel(logging.INFO)
    smsq=OsmoSmsQ.read_queue(0,True,False,'','10000','',True)
    msgs=OsmoSmsQ.build_msgs(smsq)
    sms_log.setLevel(lev)
    n = 0
    for item in msgs:
        s = item['sms']
        mid = item['mid']
        utext = item['text']
        src = s[10]
        dest = s[13]
        coding = s[8]
        n = n + 1
        print '------------------------------------------------'
        print ("Message ID: %s for %s" % (mid, dest))
        try:
            c_bts=numbering.get_current_bts(dest)
        except NumberingException as ex:
            print ex
            continue
        sms_log.debug('Type of text from OSMO: %s' % (type(utext)) ) 
        if c_bts != vpn_ip_address:
            sms_log.debug("  Found an SMS with ID %s (%s) for %s but they are at %s" % (s[0], mid, dest, c_bts))
            print "   - Re-Injecting [%s]...." % utext.encode('utf-8','replace')
            try:
                print "  Sending Message directly to RAPI on %s" % c_bts
                result = sms.send(src, dest, utext, 'unicode', c_bts)
                print "Result from SMS.send(): %s" % result
            except Exception as ex:
                sms_log.debug("Exception [ %s ] while reinjecting Message" % ex)
                continue
            else:
                print "Got no Exception, going to mark message locally as sent"
                # There's no way to no for sure if the remote kannel actually got the message,
                # or if it was succesfully entered into the osmo q.
                # So let's not delete it right away, but mark as sent and tag it somehow.
                # Or, I could submit via the VTY. Hmm.. does OpenBSC accept messages with u/k source?
                # Yes. it does.
                sq_hlr = sqlite3.connect(sq_hlr_path, timeout=5)
                sq_hlr_cursor = sq_hlr.cursor()
                for i in mid.split(','):
                    sms_log.debug("UPDATE SMS SET valid_until=9990999, sent=CURRENT_TIMESTAMP WHERE id=%s" % i)
                    sq_hlr_cursor.execute("UPDATE SMS SET valid_until=4633050,sent=CURRENT_TIMESTAMP WHERE id=?", [(i)])
                sq_hlr.commit()
                sq_hlr.close()
        else:
            print "Destination Number is here according to HLR"
        print '------------------------------------------------------------------'
except Exception as e:
    print "Top Level Exception"
    print e    
    code.interact(local=locals()) 
