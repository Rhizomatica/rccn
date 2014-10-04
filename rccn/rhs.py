############################################################################
#
# Copyright (C) 2014 tele <tele@rhizomatica.org>
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
Rhizomatica HLR Sync.
"""

import sys
import dateutil.parser as dateparser
from config import *

def update_sync_time(time):
    try:
        cur = db_conn.cursor()
        cur.execute("UPDATE meta SET value=%(time)s WHERE key='hlr_sync'", {'time': str(time)})
        db_conn.commit()
    except psycopg2.DatabaseError as e:
        hlrsync_log.error('PG_HLR unable to update hlr sync timestmap db error: %s' % e)

def get_last_sync_time():
    try:
        cur = db_conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key='hlr_sync'")
        sync_time = cur.fetchone()
        if sync_time != None:
            return int(sync_time[0])
        else:
            hlrsync_log.error('Unable to get last sync time. exit')
            sys.exit(1)
    except psycopg2.DatabaseError as e:
        hlrsync_log.error('PG_HLR database error getting last sync time')
        sys.exit(1)

try:
    rk_hlr = riak_client.bucket('hlr')
    # query riak and get list of all numbers modified since the last run
    last_run = get_last_sync_time()
    last_run_datetime = datetime.datetime.fromtimestamp(last_run).strftime('%d-%m-%Y %H:%M:%S')
    hlrsync_log.info('Sync local HLR. last run: %s' % last_run_datetime)
    #if last_run == 0:
    #    last_run = int(time.time())
    now = int(time.time())
    print 'last %s now %s' % (last_run, now)
    subscribers = rk_hlr.get_index('modified_int', last_run, now)
    total_sub = len(subscribers)
    if total_sub != 0:
        hlrsync_log.info('Found %s subscribers updated since last run' % total_sub)
        for result in subscribers.results:
            sub = rk_hlr.get(result, timeout=RIAK_TIMEOUT)
            if sub.exists:
                # update data in postgresql DB
                # check if subscriber exists if not add it to the database
                try:
                    cur = db_conn.cursor()
                    cur.execute('SELECT * FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': sub.data['msisdn']})
                    pg_sub = cur.fetchone()
                    if pg_sub != None:
                        # subscriber exists check if the updated date is different from the one in the distributed hlr
                        # if yes update data in db
                        print pg_sub[6]
                        dt = dateparser.parse(str(pg_sub[6]))
                        print dt
                        pg_ts = int(time.mktime(dt.timetuple()))
                        print pg_ts
                        print sub.data['updated']
                        if pg_ts != sub.data['updated']:
                            hlrsync_log.info('Subscriber %s has been updated in RK_HLR, update data on PG_HLR' % sub.data['msisdn'])
                            hlrsync_log.debug('msisdn[%s] home_bts[%s] current_bts[%s] authorized[%s] updated[%s]' % 
                            (sub.data['msisdn'], sub.data['home_bts'], sub.data['current_bts'], sub.data['authorized'], sub.data['updated']))
                            update_date = datetime.datetime.fromtimestamp(sub.data['updated'])
                            cur.execute('UPDATE hlr SET msisdn=%(msisdn)s, home_bts=%(home_bts)s, current_bts=%(current_bts)s, authorized=%(authorized)s, updated=%(updated)s WHERE msisdn=%(msisdn)s',
                            {'msisdn': sub.data['msisdn'], 'home_bts': sub.data['home_bts'], 'current_bts': sub.data['current_bts'], 'authorized': sub.data['authorized'], 'updated': update_date})
                        else:
                            hlrsync_log.info('Subscriber %s exists but no update necessary' % sub.data['msisdn'])
                    else:
                        hlrsync_log.info('Subscriber %s does not exist, add to the PG_HLR' % sub.data['msisdn'])
                        hlrsync_log.debug('msisdn[%s] home_bts[%s] current_bts[%s] authorized[%s] updated[%s]' % 
                        (sub.data['msisdn'], sub.data['home_bts'], sub.data['current_bts'], sub.data['authorized'], sub.data['updated']))
                        # subscriber does not exists add it to the db
                        update_date = datetime.datetime.fromtimestamp(sub.data['updated'])
                        cur.execute('INSERT INTO hlr(msisdn, home_bts, current_bts, authorized, updated) VALUES(%(msisdn)s, %(home_bts)s, %(current_bts)s, %(authorized)s, %(updated)s)',
                        {'msisdn': sub.data['msisdn'], 'home_bts': sub.data['home_bts'], 'current_bts': sub.data['current_bts'], 'authorized': sub.data['authorized'], 'updated': update_date})

                    db_conn.commit()
                except psycopg2.DatabaseError as e:
                    hlrsync_log.error('PG_HLR Database error in getting subscriber: %s' % e) 
    else:
        hlrsync_log.info('No updated subscribers found since last run')
    
    hlrsync_log.info('Update sync time')
    now = int(time.time()) 
    update_sync_time(now)

except riak.RiakError as e:
    hlrsync_log.error('RK_HLR error: %s' % e)
