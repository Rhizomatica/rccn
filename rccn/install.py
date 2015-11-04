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
