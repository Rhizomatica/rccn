############################################################################
#
# Copyright (C) 2014 tele <tele@rhizomatica.org>
#
# RCCN Installation script
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
RCCN installation script.
"""
import json
import os
import sys
import subprocess
from decimal import Decimal

import psycopg2
import psycopg2.extras
import sqlite3

from config_values import *

print 'RCCN Installation script\n'

try:
    db_conn = psycopg2.connect(
        database=pgsql_db, user=pgsql_user,
        password=pgsql_pwd, host=pgsql_host)
    db_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
except psycopg2.DatabaseError as e:
    print 'Database connection error %s' % e

print('Loading RCCN database schema... ').ljust(40),
try:
    cur = db_conn.cursor()
    cur.execute(open(rhizomatica_dir + '/db/database.sql', 'r').read())
except psycopg2.DatabaseError as e:
    print 'Database error loading schema: %s' % e
    sys.exit(1)
print 'Done'

print('Loading Rates... ').ljust(40),
try:
    cur = db_conn.cursor()
    cur.execute(open(rhizomatica_dir + '/db/rates.sql', 'r').read())
except psycopg2.DatabaseError as e:
    print 'Database error loading rates: %s' % e
    sys.exit(1)
print 'Done'

print('Adding Site Info to Riak... ').ljust(40),

riak_config = {
    'site_name': site_name,
    'postcode': postcode,
    'pbxcode': pbxcode,
    'network_name': network_name,
    'ip_address': vpn_ip_address}

riak_add_cmd = (
    "curl -X PUT http://localhost:8098/buckets/sites/keys/%s "
    "-H \"Content-Type: application/json\" "
    "-d '%s'" % (
        postcode+pbxcode,
        json.dumps(riak_config)))

os.system(riak_add_cmd)
print 'Done'

print('Adding Site Info to PGSQL... ').ljust(40),
try:
    cur = db_conn.cursor()
    cur.execute(
        "INSERT INTO site"
        "(site_name,postcode,pbxcode,network_name,ip_address) "
        "VALUES(%(site_name)s,%(postcode)s,"
        "%(pbxcode)s,%(network_name)s,%(ip_address)s)",
        {'site_name': site_name,
         'postcode': postcode,
         'pbxcode': pbxcode,
         'network_name': network_name,
         'ip_address': vpn_ip_address})
    db_conn.commit()
except psycopg2.DatabaseError as e:
    print 'Database error insert site: %s' % e
    sys.exit(1)
print 'Done'

print('Adding VoIP configuration to PGSQL... ').ljust(40),
try:
    cur = db_conn.cursor()
    cur.execute(
        "INSERT INTO providers"
        "(provider_name,username,fromuser,password,proxy,active) "
        "VALUES("
        "%(provider_name)s,%(username)s,%(fromuser)s,"
        "%(password)s,%(proxy)s,1)",
        {'provider_name': voip_provider_name,
         'username': voip_username,
         'fromuser': voip_fromuser,
         'password': voip_password,
         'proxy': voip_proxy})
    db_conn.commit()
except psycopg2.DatabaseError as e:
    print 'Database error adding VoIP provider configuration : %s' % e
    sys.exit(1)
try:
    cur = db_conn.cursor()
    cur.execute(
        'INSERT INTO dids(provider_id,phonenumber,callerid) '
        'VALUES(%(provider_id)s,%(phonenumber)s,%(callerid)s)',
        {'provider_id': 1,
         'phonenumber': voip_did,
         'callerid': voip_cli,
         'password': voip_password,
         'proxy': voip_proxy})
    db_conn.commit()
except psycopg2.DatabaseError as e:
    print 'Database error adding VoIP DID configuration: %s' % e
    sys.exit(1)
print 'Done'


def to_decimal(thing):
    """
    Convenience function that extracts decimal from a string.
    If the passed thing evaluates to False (ie, it is an empty string)
    it returns None. Otherwise it returns a decimal number.
    """
    if not thing:
        return None
    return Decimal(str(thing))

print('Adding Site configuration to PGSQL... ').ljust(40),
try:
    cur = db_conn.cursor()
    sql = (
        "INSERT INTO configuration "
        "VALUES(%(limit_local_calls)s,%(limit_local_minutes)s,"
        "%(charge_local_calls)s,%(charge_local_rate)s,"
        "%(charge_local_rate_type)s,%(charge_internal_calls)s,"
        "%(charge_internal_rate)s,%(charge_internal_rate_type)s,"
        "%(charge_inbound_calls)s,%(charge_inbound_rate)s,"
        "%(charge_inbound_rate_type)s,%(smsc_shortcode)s,"
        "%(sms_sender_unauthorized)s,%(sms_destination_unauthorized)s)"
    )
    cur.execute(
        sql,
        {'limit_local_calls': limit_local_calls,
         'limit_local_minutes': limit_local_minutes,
         'charge_local_calls': charge_local_calls,
         'charge_local_rate': to_decimal(charge_local_rate),
         'charge_local_rate_type': charge_local_rate_type,
         'charge_internal_calls': charge_internal_calls,
         'charge_internal_rate': to_decimal(charge_internal_rate),
         'charge_internal_rate_type': charge_internal_rate_type,
         'charge_inbound_calls': charge_inbound_calls,
         'charge_inbound_rate': to_decimal(charge_inbound_rate),
         'charge_inbound_rate_type': charge_inbound_rate_type,
         'smsc_shortcode': smsc_shortcode,
         'sms_sender_unauthorized': sms_sender_unauthorized,
         'sms_destination_unauthorized': sms_destination_unauthorized})
    db_conn.commit()
except psycopg2.DatabaseError as e:
    print 'Database error adding Site configuration: %s' % e
    sys.exit(1)
print 'Done'

print('Creating SMSC shortcode on HLR').ljust(40),
try:
    sq_hlr = sqlite3.connect(sq_hlr_path)
    sq_hlr_cursor = sq_hlr.cursor()
    sq_hlr_cursor.execute(
        "insert into subscriber"
        "(created,updated,imsi,name,extension,authorized) "
        "values('2013-12-27 08:00:57','2013-12-27 08:00:57',"
        "'334020111111111','SMSC',?,1)", [(smsc_shortcode)])
    sq_hlr.commit()
    sq_hlr.close()
except sqlite3.Error as e:
    print 'Database error adding SMSC shortcode: %s' % e
    sys.exit(1)
print 'Done'


print('Creating RAI admin password... ').ljust(40),
rai_pwd = subprocess.check_output(
    ['php', '-r echo password_hash("%s",PASSWORD_DEFAULT);'
     % rai_admin_pwd])
try:
    cur = db_conn.cursor()
    cur.execute(
        "INSERT INTO users(username,password,role) "
        "VALUES(%(username)s,%(password)s,'Administrator')",
        {'username': rai_admin_user, 'password': rai_pwd})
    db_conn.commit()
except psycopg2.DatabaseError as e:
    print 'Database error adding RAI admin: %s' % e
    sys.exit(1)
print 'Done'

print('Creating RRD data... ').ljust(40),
os.system("%s/bin/./network_create_rrd.sh" % rhizomatica_dir)
os.system("%s/bin/./platform_create_rrd.sh" % rhizomatica_dir)
print 'Done'

print '\nRCCN Installation completed'
