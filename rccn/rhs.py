#!/usr/bin/env python
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

import dateutil.parser as dateparser
from config import *
import random
from optparse import OptionParser
import code

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

def cleanup_hlrs():
    ''' Get all the MSISDNs that are in the local hlr with our prefix that no
    longer exist in the local subscribers table and delete them from riak and
    from our copy of the HLR '''
    try:
        cur = db_conn.cursor()
        rk_hlr = riak_client.bucket('hlr')
        sql = ("SELECT hlr.id, hlr.msisdn, hlr.home_bts, hlr.authorized, subscribers.authorized"
               " FROM hlr LEFT JOIN subscribers ON hlr.msisdn=subscribers.msisdn"
               " WHERE hlr.msisdn LIKE %(prefix)s AND subscribers.msisdn IS NULL")
        cur.execute(sql,  {'prefix': config['internal_prefix']+'%'})
        pg_gone_sub = cur.fetchall()
        hlrsync_log.info('Got %s Stale Subscribers in local HLR' % len(pg_gone_sub))
        for sub in pg_gone_sub:
            if sub[4] is None:
                try:
                    r_sub = rk_hlr.get_index('msisdn_bin', sub[1], timeout=540)
                    for imsi_key in r_sub.results:
                        r_obj = rk_hlr.get(imsi_key)
                        if r_obj.exists and r_obj.data['msisdn'] == sub[1]:
                            hlrsync_log.debug("Removing msisdn(%s), imsi(%s) from d_hlr.",
                                               sub[1], imsi_key)
                            r_obj.remove_indexes().delete()
                        elif r_obj.exists:
                            hlrsync_log.warning("msisdn(%s belongs to imsi(%s) in d_hlr.",
                                              imsi_key, r_obj.data['msisdn'])
                        else:
                            hlrsync_log.debug("imsi(%s) not in d_hlr.", imsi_key)
                except riak.RiakError as ex:
                    hlrsync_log.exception(ex)
            hlrsync_log.debug("Removing id(%s) msisdn(%s) from Local HLR." % (sub[0], sub[1]))
            sql = "DELETE FROM hlr where id = %(id)s"
            cur.execute(sql, {'id': sub[0]})
            db_conn.commit()
    except psycopg2.DatabaseError as ex:
        hlrsync_log.exception(ex)

def hlr_sync(hours,until):
    try:
        rk_hlr = riak_client.bucket('hlr')
        # query riak and get list of all numbers modified since the last run
        if hours > 0:
            last_run = int(time.time() - (hours*3600))
            last_run_datetime = datetime.datetime.fromtimestamp(last_run).strftime('%d-%m-%Y %H:%M:%S')
        else:
            last_run = get_last_sync_time()
            last_run_datetime = datetime.datetime.fromtimestamp(last_run).strftime('%d-%m-%Y %H:%M:%S')
            hlrsync_log.info('Sync local HLR. last run: %s' % last_run_datetime)
        #if last_run == 0:
        #    last_run = int(time.time())
        if until > 0:
            now = int(time.time() - (until*3600))
        else:
            now = int(time.time())
        hlrsync_log.debug('last %s now %s' % (last_run, now))
        subscribers = rk_hlr.get_index('modified_int', last_run, now)
        total_sub = len(subscribers)
        if total_sub != 0:
            if hours > 0:
                hlrsync_log.info('Found %s subscribers updated since %s' % (total_sub, last_run_datetime) )
            else:
                hlrsync_log.info('Found %s subscribers updated since last run' % total_sub)
            _c=1
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
                            # subscriber exists check if the updated date is earlier than the one in the distributed hlr
                            # if yes update data in db
                            dt = dateparser.parse(str(pg_sub[6]))
                            pg_ts = int(time.mktime(dt.timetuple()))
                            if pg_ts < sub.data['updated']:
                                hlrsync_log.info('Subscriber %s updated in RK_HLR at %s, last update on PG_HLR: %s' %
                                    ( sub.data['msisdn'], str(datetime.datetime.fromtimestamp(sub.data['updated'])), str(pg_sub[6]) ) )
                                hlrsync_log.debug('What Changed: [Home: %s] [Current: %s] [Authorized: %s]' % ( (sub.data['home_bts'] != pg_sub[3]), (sub.data['current_bts'] != pg_sub[4]), (sub.data['authorized'] != pg_sub[5]) ))
                                #code.interact(local=locals())
                                hlrsync_log.debug('msisdn[%s] home_bts[%s] current_bts[%s] authorized[%s] updated[%s]' % 
                                (sub.data['msisdn'], sub.data['home_bts'], sub.data['current_bts'], sub.data['authorized'], sub.data['updated']))
                                update_date = datetime.datetime.fromtimestamp(sub.data['updated'])
                                cur.execute('UPDATE hlr SET home_bts=%(home_bts)s, current_bts=%(current_bts)s, authorized=%(authorized)s, updated=%(updated)s WHERE msisdn=%(msisdn)s',
                                {'msisdn': sub.data['msisdn'], 'home_bts': sub.data['home_bts'], 'current_bts': sub.data['current_bts'], 'authorized': sub.data['authorized'], 'updated': update_date})
                            elif pg_ts > sub.data['updated']:
                                hlrsync_log.info('PG_HLR data is more recent for %s' % sub.data['msisdn'])
                                try:
                                    hlrsync_log.info('RIAK: pushing %s, was %s' % (pg_sub[4], sub.data['current_bts']))
                                    sub.data['current_bts'] = pg_sub[4]
                                    now = int(time.time())
                                    sub.data['updated'] = now
                                    sub.indexes = set([('modified_int', now), ('msisdn_bin', sub.data['msisdn'])])
                                    sub.store()
                                except Exception as e:
                                    print str(e)
                            else:
                                hlrsync_log.debug('[%s] Subscriber %s exists but no update necessary' % (_c, sub.data['msisdn']))
                        else:
                            hlrsync_log.info('Subscriber %s does not exist, add to the PG_HLR' % sub.data['msisdn'])
                            hlrsync_log.debug('msisdn[%s] home_bts[%s] current_bts[%s] authorized[%s] updated[%s]' % 
                            (sub.data['msisdn'], sub.data['home_bts'], sub.data['current_bts'], sub.data['authorized'], sub.data['updated']))
                            # subscriber does not exists add it to the db
                            update_date = datetime.datetime.fromtimestamp(sub.data['updated'])
                            cur.execute('INSERT INTO hlr(msisdn, home_bts, current_bts, authorized, updated) VALUES(%(msisdn)s, %(home_bts)s, %(current_bts)s, %(authorized)s, %(updated)s)',
                            {'msisdn': sub.data['msisdn'], 'home_bts': sub.data['home_bts'], 'current_bts': sub.data['current_bts'], 'authorized': sub.data['authorized'], 'updated': update_date})

                        db_conn.commit()
                        _c+=1
                    except psycopg2.DatabaseError as e:
                        hlrsync_log.error('PG_HLR Database error in getting subscriber: %s' % e) 
        else:
            hlrsync_log.info('No updated subscribers found since %s' % last_run_datetime)
        if hours == 0:
            hlrsync_log.info('Update sync time')
            now = int(time.time()) 
            update_sync_time(now)
    except riak.RiakError as e:
        hlrsync_log.error('RK_HLR error: %s' % e)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", "--cron", dest="cron", action="store_true",
        help="Running from cron, add a delay to not all hit riak at same time")
    parser.add_option("-s", "--since", dest="hours",
        help="Sync from the d_hlr since HOURS ago instead of last update")
    parser.add_option("-u", "--until", dest="until",
        help="Sync from the d_hlr until HOURS ago instead of now, requires -s")
    parser.add_option("-m", "--minutes", dest="minutes",
        help="Sync from the d_hlr since MINUTES ago (-s) instead of last update")
    parser.add_option("-e", "--expunge", dest="expunge", action="store_true",
        help="Clean removed subscribers from the HLRs")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        help="Turn on debug logging")
    (options, args) = parser.parse_args()
    
    if options.debug:
        hlrsync_log.setLevel(logging.DEBUG)
    else:
        hlrsync_log.setLevel(logging.INFO)

    if options.cron:
        wait=random.randint(0,120)
        print "Waiting %s seconds..." % wait
        time.sleep(wait)

    if options.expunge:
        cleanup_hlrs()
        sys.exit()

    if options.hours or options.minutes:
        if options.until:
            until=int(options.until)
        else:
            until=0
        if options.minutes:
            hours=float(options.minutes+'.00')/60
        else:
            hours=int(options.hours)
        hlr_sync(hours,until)
    else:
        hlr_sync(0,0)
