############################################################################
#
# Copyright (C) 2015 tele <tele@rhizomatica.org>
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

""" Populate Distributed Riak database with site and subscribers info  """

import sqlite3
import time
import riak
from riak.transports.pbc.transport import RiakPbcTransport

from config_values import site_name, vpn_ip_address, postcode, pbxcode, network_name, sq_hlr_path

prefix = postcode + pbxcode

riak_client = riak.RiakClient(host=vpn_ip_address, pb_port=8087, protocol='pbc')

sq_hlr = sqlite3.connect(sq_hlr_path)
sq_hlr_cursor = sq_hlr.cursor()
sq_hlr_cursor.execute("select * from Subscriber where extension like '%(prefix)s' " % {'prefix': prefix+'%'})
subscribers = sq_hlr_cursor.fetchall()


print 'Create site'
rk_site = riak_client.bucket('sites')
rk_site.set_property('last_write_wins', 1)
rk_site.set_property('allow_mult', 0)
rk_site.set_property('n_val', 10)
rk_site.set_property('r', 1)
rk_site.set_property('w', 1)
rk_site.set_property('dw', 1)
rk_site.new(prefix, data={"site_name": site_name, "postcode": postcode, "pbxcode": pbxcode, "network_name": network_name, "ip_address": vpn_ip_address}).store()

rk_hlr = riak_client.bucket('hlr')
rk_hlr.set_property('last_write_wins', 1)
rk_hlr.set_property('allow_mult', 0)
rk_hlr.set_property('n_val', 10)
rk_hlr.set_property('r', 1)
rk_hlr.set_property('w', 1)
rk_hlr.set_property('dw', 1)

for sub in subscribers:
    imsi = str(sub[3])
    msisdn = sub[5]
    authorized = sub[6]

    now = int(time.time())

    print 'Provisioning imsi[%s] msisdn[%s] home_bts[%s] current_bts[%s] authorized[%s] on distributed HLR' % (imsi, msisdn, vpn_ip_address, vpn_ip_address, authorized)
    dhlr = rk_hlr.new(imsi, data={"msisdn": msisdn, "home_bts": vpn_ip_address, "current_bts": vpn_ip_address, "authorized": authorized, "updated": now})
    dhlr.add_index('msisdn_bin', msisdn)
    dhlr.add_index('modified_int', now)
    dhlr.store()

