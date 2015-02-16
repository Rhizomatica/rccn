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

    def get_site(self):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * from site')
            site_conf = cur.fetchone()
            if site_conf != None:
                return site_conf
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error getting site info: %s' % e)

    def get_site_config(self):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * from configuration')
            site_conf = cur.fetchone()
            if site_conf != None:
                return site_conf
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error getting site config: %s' % e)
    
    def get_locations(self):
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
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT limit_local_calls,limit_local_minutes FROM configuration')
            limit = cur.fetchone()
            if limit != None:
                return (limit[0], limit[1] * 60)
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error checking for local calls limit: %s' % e)

    
    def check_charge_local_calls(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT charge_local_calls FROM configuration')
            charge = cur.fetchone()
            if charge != None:
                return charge[0]
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error checking for charge local calls: %s' % e)
           
    def get_charge_local_calls(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT charge_local_rate,charge_local_rate_type FROM configuration')
            charge = cur.fetchone()
            if charge != None:
                return charge
            else:
                raise ConfigurationException('No configuration for for charging local calls')
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error getting info charging local calls: %s' % e)

    def check_charge_inbound_calls(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT charge_inbound_calls FROM configuration')
            charge = cur.fetchone()
            if charge != None:
                return charge[0]
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error checking for charge inbound calls: %s' % e)
            
    def get_charge_inbound_calls(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT charge_inbound_rate,charge_inbound_rate_type FROM configuration')
            charge = cur.fetchone()
            if charge != None:
                return charge
            else:
                raise ConfigurationException('No configuration found for charging inbound calls')
        except psycopg2.DatabaseError as e:
            raise ConfigurationException('Database error getting info for charging inbound calls: %s' % e)
