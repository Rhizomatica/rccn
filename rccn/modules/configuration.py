############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Configuration module
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

class ConfigurationException(Exception):
    pass

class Configuration:
    """ Configuration module """

    def get_site(self):
	""" Get site information """
	return {'site_name': site_name, 'postcode': postcode, 'pbxcode': pbxcode,
		'network_name': network_name, 'ip_address': vpn_ip_address}

    def get_site_config(self):
	""" Get site settings """
	return {'limit_local_calls': limit_local_calls, 'limit_local_minutes': limit_local_minutes,
		'charge_local_calls': charge_local_calls, 'charge_local_rate': charge_local_rate,
		'charge_local_rate_type': charge_local_rate_type, 'charge_internal_calls': charge_internal_calls,
		'charge_internal_rate': charge_internal_rate, 'charge_internal_rate_type': charge_internal_rate_type,
		'charge_inbound_calls': charge_inbound_calls, 'charge_inbound_rate': charge_inbound_rate,
		'charge_inbound_rate_type': charge_inbound_rate_type}
    
    def get_locations(self):
	""" Get list of locations """
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM locations')
            locations = cur.fetchall()
            if locations != None:
                return locations
	    else:
		return ""
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error getting locations: %s' % e)
    
    def get_local_calls_limit(self):
	""" Get local call limit in seconds """
	return (limit_local_calls == 1) ? (limit_local_minutes * 60) : False
    
    def check_charge_local_calls(self):
	""" Check if local calls need to be charged """
	return (charge_local_calls == 1) ? True : False	
           
    def get_charge_local_calls(self):
	""" Get settings to charge local calls """
	return {'charge_local_rate': charge_local_rate, 
        	'charge_local_rate_type': charge}

    def check_charge_inbound_calls(self):
	""" Check if inbound calls need to be charged """
	return (charge_inbound_calls == 1) ? True : False
            
    def get_charge_inbound_calls(self):
	""" Get settings to charge inbound calls """
	return {'charge_inbound_rate': charge_inbound_rate, 
		'charge_inbound_rate_type': charge_inbound_rate_type}
