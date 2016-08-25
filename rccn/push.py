#!/usr/bin/env python
"""Get info from Riak about an extension"""
############################################################################
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
import socket
import datetime
import obscvty
#import riak
from config import *

def check(recent, days=10):
    """ Get sub from the local PG db and see their status in riak """
    cur = db_conn.cursor()
    if recent == 0:
        cur.execute("SELECT msisdn,name from Subscribers where authorized=1")
    if recent == 1:
        sql = "SELECT msisdn,created FROM Subscribers WHERE created > NOW() -interval '%s days'" % days
        cur.execute(sql)
    if cur.rowcount > 0:
        print 'Subscriber Count: %s ' % (cur.rowcount)
        _subs=cur.fetchall()
        for msisdn,name in _subs:
            print '----------------------------------------------------'
            print "Checking %s %s" % (msisdn, name)
	    imsi=osmo_ext2imsi(msisdn)
	    if imsi:
                print "Local IMSI: \033[96m%s\033[0m" % (imsi)
                get(msisdn, imsi)
            else:
                print "\033[91;1mLocal Subscriber from PG Not Found on OSMO HLR!\033[0m"
            print '----------------------------------------------------\n'

def get(msisdn, imsi):
    """Do the thing"""
    riak_client = riak.RiakClient(
    host='10.23.0.3',
    pb_port=8087,
    protocol='pbc')
    bucket = riak_client.bucket('hlr')
    sub = Subscriber()
    num = Numbering()
    try:
        riak_imsi = bucket.get_index('msisdn_bin', msisdn).results
        if not len(riak_imsi):
            print '\033[93mExtension %s not found\033[0m, adding to D_HLR' % (msisdn)
            sub._provision_in_distributed_hlr(imsi, msisdn)
        else:
            if imsi != riak_imsi[0]:
                print "\033[91;1mIMSIs do not Match!\033[0m (%s)" % riak_imsi[0]  
		print "%s Belongs to %s" % (riak_imsi[0], num.get_msisdn_from_imsi(riak_imsi[0]))
                return False
            print 'Extension: \033[95m%s\033[0m-%s-\033[92m%s\033[0m ' \
                  'has IMSI \033[96m%s\033[0m' % (msisdn[:5], msisdn[5:6], msisdn[6:], riak_imsi[0])
            data = bucket.get(riak_imsi[0]).data
            if data['authorized']:
                print "Extension: Authorised"
            else:
                print "Extension: \033[91mNOT\033[0m Authorised"
            try:
                host = socket.gethostbyaddr(data['home_bts'])
                home = host[0]
                host = socket.gethostbyaddr(data['current_bts'])
                current = host[0]
            except Exception as ex:
                home = data['home_bts']
                current = data['current_bts']
            print " Home BTS: %s" % (home)
            print "Last Seen: %s, %s" % ( 
                  current, 
                  datetime.datetime.fromtimestamp(data['updated']).ctime() )
    except Exception as ex:
        print ex


def osmo_ext2imsi(ext):
    try:
        vty = obscvty.VTYInteract('OpenBSC', '127.0.0.1', 4242)
        cmd = 'show subscriber extension %s' % (ext)
        t = vty.command(cmd)        
        m=re.compile('IMSI: ([0-9]*)').search(t)
        if m:
            return m.group(1)
        else: 
            return False
    except:
        print sys.exc_info()[1]
        return False

if __name__ == '__main__':
    if len(sys.argv) == 1:
	check(0)
    else:
        if sys.argv[1] == 'recent':
            if len(sys.argv) == 3:
                check(1,sys.argv[2])
            else:
                check(1)
            

