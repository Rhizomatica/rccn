#!/usr/bin/python
############################################################################
#
# Copyright (C) 2014 tele <tele@rhizomatica.org>
# Copyright (C) 2018 keith <keith@rhizomatica.org>
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

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import sys
import subprocess
from decimal import Decimal
from optparse import OptionParser
import psycopg2
import psycopg2.extras
import sqlite3

from config_values import *

def to_decimal(thing):
    """
    Convenience function that extracts decimal from a string.
    If the passed thing evaluates to False (ie, it is an empty string)
    it returns None. Otherwise it returns a decimal number.
    """
    if not thing:
        return None
    return Decimal(str(thing))

def db_init(debug):
    print('Loading RCCN database schema... '.ljust(40))

    try:
        cur.execute(open(rhizomatica_dir + '/db/database.sql', 'r').read())
    except psycopg2.DatabaseError as e:
        print('Database error loading schema: %s' % e)
    else:
        print('Done')

    print('Loading Rates... '.ljust(40))

    try:
        cur.execute(open(rhizomatica_dir + '/db/rates.sql', 'r').read())
    except psycopg2.DatabaseError as e:
        print('Database error loading rates: %s' % e)
    else:
        print('Done')

def db_prefix(table):
    print('Adding PREFIX table... '.ljust(40))
    try:
        cur.execute(
            "CREATE TABLE " +  table + " ("
            "a VARCHAR(33) NOT NULL, "
            "b DECIMAL NOT NULL, "
            "d DECIMAL NOT NULL)"
        )
    except psycopg2.DatabaseError as e:
        print('Database error creating prefix table: %s' % e)
        return False
    else:
        print('Done')
        return True

def db_prefix_data(sql_file):
    print('Loading prefix data... '.ljust(40))
    try:
        cur.execute(open(rhizomatica_dir + '/db/' + sql_file + '.sql', 'r').read())
    except psycopg2.DatabaseError as e:
        print('Database error loading data: %s' % e)
    else:
        print('Done')

def db_site(debug):
    print('Adding Site Info to PGSQL... '.ljust(40))
    try:
        cur.execute("DELETE FROM site")
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
        print('Database error inserting site data: %s' % e)
    else:
        print('Done')

def db_voip(debug):
    print('Adding VoIP configuration to PGSQL... '.ljust(40))
    try:
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
        print('Database error adding VoIP provider configuration : %s' % e)
    else:
        print("Providers Done")

    try:
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
        print('Database error adding VoIP DID configuration: %s' % e)
    else:
        print('DIDs Done')


    print('Adding Site configuration to PGSQL... '.ljust(40))
    try:
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
        print('Database error adding Site configuration: %s' % e)
    else:
        print('Done')

def osmo_hlr(debug):
    print('Creating SMSC shortcode on HLR'.ljust(40))
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
        print('Database error adding SMSC shortcode: %s' % e)
    else:
        print('Done')

def admin_pw(debug):
    print('Creating User for RAI ... Username: "%s", Password: "%s"\n'.ljust(40) % (rai_admin_user, rai_admin_pwd))
    rai_pwd = subprocess.check_output(
        ['php', '-r echo password_hash("%s",PASSWORD_DEFAULT);'
         % rai_admin_pwd])
    try:
        cur.execute(
            "INSERT INTO users(id,username,password,role) "
            "VALUES(1,%(username)s,%(password)s,'Administrator') "
            "ON CONFLICT (id) DO "
            "UPDATE SET id=1, username=%(username)s, password=%(password)s",
            {'username': rai_admin_user, 'password': rai_pwd})
        db_conn.commit()
    except psycopg2.DatabaseError as e:
        print('Database error adding RAI admin: %s' % e)
    else:
        print('Done')

def rrd_date(debug):
    print('Creating RRD data... '.ljust(40))
    os.system("%s/bin/./network_create_rrd.sh" % rhizomatica_dir)
    os.system("%s/bin/./platform_create_rrd.sh" % rhizomatica_dir)
    print('Done')

def riak_add():
    print('Adding Site Info to Riak... '.ljust(40))

    riak_config = {
        'site_name': site_name,
        'postcode': postcode,
        'pbxcode': pbxcode,
        'network_name': network_name,
        'ip_address': vpn_ip_address}

    riak_add_cmd = (
        "curl -X PUT http://%s:8098/buckets/sites/keys/%s "
        "-H \"Content-Type: application/json\" "
        "-d '%s'" % (
            riak_ip_address,
            postcode+pbxcode,
            json.dumps(riak_config)))

    os.system(riak_add_cmd)
    print('Done')

print('RCCN Installation script\n')

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f", "--full", dest="full", action="store_true",
        help="Full Install; Run all the installation routines")
    parser.add_option("-u", "--user", dest="user", action="store_true",
        help="Configure the User in the user database (resets the password to whatever is in the python config)")
    parser.add_option("-r", "--riak", dest="riak", action="store_true",
        help="Add site info to Riak")
    parser.add_option("-s", "--sqlite", dest="sqlite", action="store_true",
        help="Only Setup the OsmoCom NITB Sqlite3 HLR database. (nitb must be run once before you do this)")
    parser.add_option("-p", "--prefix", dest="prefix",
        help="Only create and insert the data for the prefix table. (not run by default)")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Turn on debug logging")
    (options, args) = parser.parse_args()

    debug = False
    if options.debug:
        debug = True

try:
    db_conn = psycopg2.connect(
        database=pgsql_db, user=pgsql_user,
        password=pgsql_pwd, host=pgsql_host)
    db_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = db_conn.cursor()
except psycopg2.DatabaseError as e:
    print('Database connection error %s' % e)
    sys.exit(1)

if options.full:
    db_init(debug)
    db_site(debug)
    db_voip(debug)
    osmo_hlr(debug)
    admin_pw(debug)
    rrd_date(debug)

if options.user:
    admin_pw(debug)

if options.sqlite:
    osmo_hlr(debug)

if options.prefix:
    sql_file = rhizomatica_dir + '/db/' + options.prefix + '.sql'
    if os.path.isfile(sql_file):
        if db_prefix(options.prefix):
            db_prefix_data(options.prefix)
    else:
        print("%s not found." % sql_file)

if options.riak:
    riak_add()

print('\nRCCN Installation completed')
