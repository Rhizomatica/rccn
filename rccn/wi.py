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
import riak

def get():
    """Do the thing"""
    riak_client = riak.RiakClient(
    host='10.23.0.3',
    pb_port=8087,
    protocol='pbc')
    bucket = riak_client.bucket('hlr')
    try:
        msisdn = sys.argv[1]
        imsi = bucket.get_index('msisdn_bin', msisdn).results
        if not len(imsi):
            print '\033[93mExtension %s not found\033[0m' % (msisdn)
        else:  
            print '----------------------------------------------------'
            print 'Extension: \033[95m%s\033[0m-%s-\033[92m%s\033[0m ' \
                  'has IMSI \033[96m%s\033[0m' % (msisdn[:5], msisdn[5:6], msisdn[6:], imsi[0])
            data = bucket.get(imsi[0]).data
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
            print '----------------------------------------------------'
    except Exception as ex:
        print ex

if __name__ == '__main__':
    get()
