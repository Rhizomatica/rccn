############################################################################
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Subscriber module
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

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import obscvty
import psycopg2
import riak
import socket
import sqlite3
import time
from unidecode import unidecode

from config import (db_conn, sq_hlr_path, config, api_log, roaming_log, RIAK_TIMEOUT, NoDataException)
from decimal import Decimal
from ESL import ESLconnection

class SubscriberException(Exception):
    pass

class Subscriber:
    """Module encapsulating access to subscriber specific data.
    Args:
        local_db_conn: The connection used for local datastore queries, defaults to the global db_conn
        hlr_db_path: The path of the sqlite3 database of the hlr, defaults to global config
        vty: The provider of a vty connection to the operational HLR, defaults to obscvty
        riak_client: The riak distributed hlr client, defaults to no riak connection
        riak_timeout: The wait timeout for riak operations
    """

    def __init__(
            self,
            local_db_conn=db_conn,
            hlr_db_path=sq_hlr_path,
            riak_client=None,
            riak_timeout=RIAK_TIMEOUT
    ):
        self._local_db_conn = local_db_conn
        self._hlr_db_path = hlr_db_path
        self._riak_client = riak_client
        self._riak_timeout = riak_timeout

    def get_balance(self, subscriber_number):
        # check if extension if yes add internal_prefix
        if len(subscriber_number) == 5:
            subscriber_number = config['internal_prefix']+subscriber_number

        try:
            cur = self._local_db_conn.cursor()
            cur.execute("SELECT balance FROM subscribers WHERE msisdn = %(number)s AND authorized=1", {'number': subscriber_number})
            balance = cur.fetchone()
            if balance != None:
                cur.close()
                return balance[0]
            else:
                cur.close()
                raise SubscriberException("Error in getting subscriber balance")
        except psycopg2.DatabaseError as e:
            cur.close()
            raise SubscriberException('Database error in getting subscriber balance: %s' % e)

    def set_balance(self, subscriber_number, balance):
        # check if extension if yes add internal_prefix
        if len(subscriber_number) == 5:
            subscriber_number = config['internal_prefix']+subscriber_number
        try:
            cur = self._local_db_conn.cursor()
            cur.execute("UPDATE subscribers SET balance = %(balance)s WHERE msisdn = %(number)s", {'balance': Decimal(str(balance)), 'number': subscriber_number})
            self._local_db_conn.commit()
        except psycopg2.DatabaseError as e:
            cur.close()
            raise SubscriberException('Database error updating balance: %s' % e)


    def is_authorized(self, subscriber_number, auth_type):
        # auth type 0 check subscriber without checking extension
        # auth type 1 check subscriber with checking extension
        try:
            cur = self._local_db_conn.cursor()

            if auth_type == 1:
                # check if extension if yes add internal_prefix used to find the subscriber by the extension
                if len(subscriber_number) == 5:
                    subscriber_number = config['internal_prefix']+subscriber_number

            cur.execute("SELECT msisdn FROM subscribers WHERE msisdn = %(number)s AND authorized=1", {'number': subscriber_number})
            sub = cur.fetchone()
            if sub != None:
                return True
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise SubscriberException('Database error in checking subscriber authorization: %s' % e)

    def get_local_msisdn(self, imsi):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE imsi=%(imsi)s AND lac > 0" % {'imsi': imsi})
            connected = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if len(connected) <= 0:
                raise SubscriberException('imsi %s not found' % imsi)
            return connected[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_local_extension(self, imsi):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE imsi=%(imsi)s" % {'imsi': imsi})
            connected = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            if len(connected) <= 0:
                raise SubscriberException('imsi %s not found' % imsi)
            return connected[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])
        except TypeError as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: number not found')

    def get_msisdn_from_imei(self, imei):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql = ('SELECT Equipment.imei, Subscriber.imsi, '
                   'Subscriber.extension, Subscriber.updated '
                   'FROM Equipment, EquipmentWatch, Subscriber '
                   'WHERE EquipmentWatch.equipment_id=Equipment.id '
                   'AND EquipmentWatch.subscriber_id=Subscriber.id '
                   'AND Equipment.imei=? '
                   'ORDER BY Subscriber.updated DESC LIMIT 1;')
            print(sql)
            sq_hlr_cursor.execute(sql, [(imei)])
            extensions = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return extensions
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_imei_autocomplete(self, partial_imei=''):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql = 'SELECT DISTINCT Equipment.imei FROM Equipment '
            if partial_imei != '':
                sql += 'WHERE Equipment.imei LIKE ? ORDER BY Equipment.imei ASC'
                sq_hlr_cursor.execute(sql, [(partial_imei+'%')])
            else:
                sq_hlr_cursor.execute(sql)
            imeis = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if imeis == []:
                return []
            if len(imeis) == 1:
                data = self.get_msisdn_from_imei(imeis[0][0])
                return data
            else:
                return imeis
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all(self):
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT * FROM subscribers')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                cur.close()
                return sub
            else:
                cur.close()
                raise SubscriberException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_notpaid(self, location=False):
        try:
            cur = self._local_db_conn.cursor()
            if location:
                cur.execute('SELECT * FROM subscribers WHERE subscription_status = 0 and location = %s', (location, ))
            else:
                cur.execute('SELECT * FROM subscribers WHERE subscription_status = 0')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise NoDataException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_authorized(self, location=False):
        try:
            cur = self._local_db_conn.cursor()
            if location:
                cur.execute('SELECT * FROM subscribers WHERE authorized = 1 and location = %s', (location, ))
            else:
                cur.execute('SELECT * FROM subscribers WHERE authorized = 1')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise NoDataException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_unauthorized(self, location=False):
        try:
            cur = db_conn.cursor()
            if location:
                cur.execute('SELECT * FROM subscribers WHERE authorized = 0 and location = %s', (location, ))
            else:
                cur.execute('SELECT * FROM subscribers WHERE authorized = 0')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise NoDataException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_5digits(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT id, extension FROM subscriber WHERE length(extension) = 5 AND extension != ?", [(config['smsc'])])
            extensions = sq_hlr_cursor.fetchall()
            if extensions == []:
                raise NoDataException('No extensions found')
            else:
                sq_hlr.close()
                return extensions
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_expire(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension,expire_lu FROM subscriber WHERE length(extension) = 11")
            subscribers = sq_hlr_cursor.fetchall()
            if subscribers == []:
                raise SubscriberException('No subscribers found')
            else:
                sq_hlr.close()
                return subscribers
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_sip_connected(self):
        try:
            _sip_connected = []
            con = ESLconnection("127.0.0.1", "8021", "ClueCon")
            e = con.api("show registrations")
            reg=e.getBody()
            lines=reg.split('\n')
            for line in lines[1:]:
                vals=line.split(',')
                if len(vals) < 10:
                    return _sip_connected
                _sip_connected.append([vals[0]])
        except Exception as ex:
            api_log.info('Exception: %s' % ex)

    def get_all_connected(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE extension LIKE ? AND lac > 0", [(config['internal_prefix']+'%')])
            connected = sq_hlr_cursor.fetchall()
            if connected == []:
                raise SubscriberException('No connected subscribers found')
            else:
                sq_hlr.close()
                return connected

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_disconnected(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE extension LIKE ? AND lac = 0", [(config['internal_prefix']+'%')])
            disconnected = sq_hlr_cursor.fetchall()
            if disconnected == []:
                raise SubscriberException('No disconnected subscribers found')
            else:
                sq_hlr.close()
                return disconnected

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_unregistered(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension,imsi FROM subscriber WHERE length(extension) = 5 AND lac > 0")
            unregistered = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return unregistered

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_foreign(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension,imsi FROM subscriber WHERE length(extension) = 11 AND extension NOT LIKE ? AND lac > 0", ( [config['internal_prefix']+'%']) )
            foreign = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return foreign
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_since(self, days):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE (length(extension) = 5 OR extension NOT LIKE \"%(prefix)s%%\") AND extension != %(smsc)s AND updated < date('now', '-%(days)s days')" % {'days': days, 'smsc': config['smsc'], 'prefix': config['internal_prefix']})
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_roaming(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE length(extension) = 11 AND extension NOT LIKE '%s%%' AND lac = 0" % config['internal_prefix'])
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_roaming_since(self, days):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            _sql=("SELECT extension FROM subscriber WHERE length(extension) = 11 AND extension NOT LIKE \"%(prefix)s%%\" AND lac = 0 AND updated < date('now', '-%(days)s days')" % {'days': days, 'prefix': config['internal_prefix']})
            sq_hlr_cursor.execute(_sql)
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_roaming_ours(self):
        try:
            b = self._riak_client.bucket('hlr')
            b.set_property('r',1)
            # Lets do it by site.
            #s = self._riak_client.bucket('sites')
            #s.set_property('r',1)
            #sites=s.get_keys()
            # We only actually care here about us
            sites=[config['internal_prefix']]
            results=[]
            for site in sites:
                roaming_log.info('Start searching site: %s' % site)
                keys = b.get_index('msisdn_bin',site,str(int(site)+1)).results
                roaming_log.info('Got %s keys' % len(keys) )
                for imsi in keys:
                    data = b.get(imsi).data
                    if type(data) is not dict:
                        continue
                    if data['home_bts'] != data['current_bts']:
                        results.append(imsi)
            return results
        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')

    def get_all_roaming(self):
        try:
            results = self._riak_client.add('hlr').map(
                """
            function(value, keyData, arg) {
                if (value.values[0].metadata["X-Riak-Deleted"] === undefined) {
                    var data = Riak.mapValuesJson(value)[0];
                    if ((data.home_bts == "%s") && (data.current_bts != data.home_bts)) {
                        return [value.key];
                    } else {
                        return [];
                    }
                } else {
                    return [];
                }
            }
                """ % config['local_ip']
                ).run(timeout=600000)
            if not results:
                return []
            return results
        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')


    def get_online(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT count(*) FROM subscriber WHERE length(extension) = 11 AND lac > 0")
            connected = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return connected[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_offline(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT count(*) FROM subscriber WHERE length(extension) = 11 AND lac = 0")
            offline = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return offline[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_roaming(self):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT count(*) FROM subscriber WHERE length(extension) = 11 AND extension not LIKE ? AND lac > 0", ([config['internal_prefix']+'%']) )
            roaming = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return roaming[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])


    def get_unpaid_subscription(self):
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers WHERE subscription_status=0')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_paid_subscription(self):
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers WHERE subscription_status=1')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_unauthorized(self):
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers WHERE authorized=0')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get(self, msisdn):
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT * FROM subscribers WHERE msisdn = %(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
                sub = cur.fetchone()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscriber found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscriber: %s' % e)

    def set_lac(self, imsi, lac):
        ''' I fixed this, but don't use it. Dont write to the sqlite3. '''
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            print('Update lac %s %s' % (imsi, lac))
            sq_hlr_cursor.execute('UPDATE subscriber SET lac=? WHERE imsi=?', (lac, imsi) )
            sq_hlr.commit()
            sq_hlr.close()
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error updating subscriber lac: %s' % e.args[0])

    def expire_lu(self, msisdn):
        appstring = 'OpenBSC'
        appport = 4242
        try:
            vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
            cmd = 'enable'
            vty.command(cmd)
            cmd = 'subscriber extension %s expire' % (msisdn)
            ret = vty.command(cmd)
            api_log.debug('VTY: %s' % ret)
            if ret:
                raise SubscriberException('VTY: %s' % ret)
        except IOError as e:
            api_log.debug('Exception in expire_lu! %s' % e)
            pass

    def add(self, msisdn, name, balance, location='', equipment=''):
        if len(msisdn) == 15:
            # lookup extension by imsi
            extension = self.get_local_extension(msisdn)
            if len(extension) == 11:
                extension=extension[-5:]
            imsi = msisdn
            msisdn = extension
        else:
            imsi = self._get_imsi(msisdn)

        subscriber_number = config['internal_prefix'] + msisdn
        # check if subscriber already exists
        if self._check_subscriber_exists(msisdn):
            try:
                # get a new extension
                msisdn = self._get_new_msisdn(msisdn, name)
                subscriber_number = config['internal_prefix'] + msisdn
                self._provision_in_database(subscriber_number, name, balance, location, equipment)
            except SubscriberException as e:
                # revert back the change on SQ_HLR
                self._authorize_subscriber_in_local_hlr(subscriber_number, msisdn, name)
                raise SubscriberException('Error provisioning new number %s, please try again. ERROR: %s' % (msisdn, str(e)))
        else:
            try:
                self._authorize_subscriber_in_local_hlr(msisdn, subscriber_number, name)
                self._provision_in_database(subscriber_number, name, balance, location, equipment)
            except SubscriberException as e:
                # revert back the change on SQ_HLR
                self._authorize_subscriber_in_local_hlr(subscriber_number, msisdn, name)
                raise SubscriberException('Error provisioning the number %s, please try again. ERROR: %s' % (msisdn, str(e)))
                
        return msisdn

    def _check_subscriber_exists(self, msisdn):
        try:
            api_log.debug('Check exists: %s' % msisdn)
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('SELECT extension FROM subscriber WHERE extension=?', [(config['internal_prefix'] + msisdn)])
            entry = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if len(entry) <= 0:
                return False
            return True
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error sub: %s' % e.args[0])

    def _get_new_msisdn(self, msisdn, name):
        try:
            newext=msisdn
            while True:
                # There was an Infinite loop here if msisdn + 1 does exist we never get out
                # Not ever sure what this is for.                
                # if last ext available reset to 0
                if newext == 99999:
                    newext = 00000
                # increment msisdn of one and check if exists
                newexti = int(newext) + 1
                newext = str(newexti)
                api_log.debug('New Extension: %s' % newext)
                if not self._check_subscriber_exists(newext):
                    try:
                        self._authorize_subscriber_in_local_hlr(msisdn, config['internal_prefix'] + newext, name)
                    except:
                        raise SubscriberException('SQ_HLR error adding new extension %s to the db' % newext)
                    return newext
        except:
            raise SubscriberException('Error in getting new msisdn for existing subscriber')


    def update(self, msisdn, name, number):
        imsi = self._get_imsi(msisdn)
        self._authorize_subscriber_in_local_hlr(msisdn, number, name)
        self.update_location(imsi, number, True)

    def update_location(self, imsi, msisdn, ts_update=False):
        try:
            rk_hlr = self._riak_client.bucket('hlr')
            subscriber = rk_hlr.get(str(imsi), timeout=self._riak_timeout)
            roaming_log.info('RIAK: pushing %s, was %s' % (config['local_ip'],subscriber.data['current_bts']))
            subscriber.data['current_bts'] = config['local_ip']
            if ts_update:
                now = int(time.time())
                subscriber.data['updated'] = now
                subscriber.indexes = set([('modified_int', now), ('msisdn_bin', subscriber.data['msisdn'])])
            subscriber.store()

            if ts_update:
                self._update_location_pghlr(subscriber)

        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')
        except SubscriberException as e:
            raise SubscriberException('PG_HLR error updating info: %s' % e)

    def _update_location_pghlr(self, subscriber):
        try:
            cur = self._local_db_conn.cursor()
            update_date = datetime.datetime.fromtimestamp(subscriber.data['updated'])
            cur.execute(
                'UPDATE hlr SET msisdn = %(msisdn)s, home_bts = %(home_bts)s, current_bts = %(current_bts)s, '
                'authorized = %(authorized)s, updated = %(updated)s WHERE msisdn=%(msisdn)s',
                {
                    'msisdn': subscriber.data['msisdn'],
                    'home_bts': subscriber.data['home_bts'],
                    'current_bts': subscriber.data['current_bts'],
                    'authorized': subscriber.data['authorized'],
                    'updated': update_date
                }
            )
            self._local_db_conn.commit()
        except psycopg2.DatabaseError as e:
            raise SubscriberException('Database error: %s' % e)

    def update_location_local_hlr(self, extension, current_bts=False):
        try:
            cur = self._local_db_conn.cursor()
            if current_bts is False:
                cur.execute(
                    'UPDATE hlr SET current_bts = home_bts, updated = %(updated)s WHERE msisdn = %(msisdn)s',
                    {'msisdn': extension, 'updated': "now()"}
                )
            else:
                cur.execute(
                    'UPDATE hlr SET current_bts = %(current_bts)s, updated = %(updated)s WHERE msisdn = %(msisdn)s',
                    {'msisdn': extension, 'current_bts': current_bts, 'updated': "now()"}
                )
            self._local_db_conn.commit()
        except psycopg2.DatabaseError as e:
            raise SubscriberException('Database error: %s' % e)

    def delete(self, msisdn):
        subscriber_number = msisdn[-5:]
        appstring = 'OpenBSC'
        appport = 4242
        try:
            vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
            cmd = 'enable'
            vty.command(cmd)
            cmd = 'subscriber extension %s extension %s' % (msisdn, subscriber_number)
            vty.command(cmd)
        except:
            pass

        # PG_HLR delete subscriber
        try:
            cur = self._local_db_conn.cursor()
            cur.execute(
                'DELETE FROM subscribers WHERE msisdn = %(msisdn)s',
                {'msisdn': msisdn}
            )
            cur.execute(
                'DELETE FROM hlr WHERE msisdn=%(msisdn)s',
                {'msisdn': msisdn}
            )

            # TODO(matt9j) This might leak a transaction if the subscriber is not in the hlr
            if cur.rowcount > 0:
               self._local_db_conn.commit()
            cur.close()
        except psycopg2.DatabaseError as e:
            cur.close()
            pass

        self._delete_in_distributed_hlr(msisdn)

    def purge(self, msisdn):
        # delete subscriber on the HLR sqlite DB
        appstring = 'OpenBSC'
        appport = 4242
        vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
        cmd = 'enable'
        vty.command(cmd)
        cmd = 'subscriber extension %s delete' % msisdn
        vty.command(cmd)

    def print_vty_hlr_info(self, msisdn):
        appstring = 'OpenBSC'
        appport = 4242
        vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
        cmd = 'enable'
        vty.command(cmd)
        cmd = 'show subscriber extension %s' % msisdn
        return vty.command(cmd)    
        

    def authorized(self, msisdn, auth):
        # auth 0 subscriber disabled
        # auth 1 subscriber enabled
        # disable/enable subscriber in Osmo
        try:
            appstring = 'OpenBSC'
            appport = 4242
            vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
            cmd = 'enable'
            vty.command(cmd)
            cmd = 'subscriber extension %s authorized %s' % (msisdn, auth)
            vty.command(cmd)
        except:
            print("VTY Exception")
            pass
                
        # disable/enable subscriber on PG Subscribers
        try:
            cur = self._local_db_conn.cursor()
            cur.execute(
                'UPDATE subscribers SET authorized = %(auth)s WHERE msisdn = %(msisdn)s',
                {'auth': auth, 'msisdn': msisdn}
            )
            if cur.rowcount > 0:
                self._local_db_conn.commit()
            else:
                self._local_db_conn.rollback()
                raise SubscriberException('PG_HLR Subscriber not found')
        except psycopg2.DatabaseError as e:
            self._local_db_conn.rollback()
            raise SubscriberException('PG_HLR error changing auth status: %s' % e)

        try:
            now = int(time.time())
            imsi=self._get_imsi(msisdn)
            rk_hlr = self._riak_client.bucket('hlr')
            subscriber = rk_hlr.get(imsi, timeout=RIAK_TIMEOUT)
            if subscriber.exists:
                subscriber.data['authorized'] = auth
                subscriber.data['updated'] = now
                subscriber.indexes = set([('modified_int', now), ('msisdn_bin', subscriber.data['msisdn'])])
                subscriber.store()
            else:
                # There's no riak entry for this subscriber, add it.
                self._provision_in_distributed_hlr(imsi, msisdn)
        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')

    def subscription(self, msisdn, status):
        # status 0 - subscription not paid
        # status 1 - subscription paid
        try:
            cur = self._local_db_conn.cursor()
            cur.execute(
                'SELECT subscription_status FROM subscribers WHERE msisdn = %(msisdn)s',
                {'msisdn': msisdn}
            )
            if cur.rowcount > 0:
                prev_status = cur.fetchone()
            else:
                self._local_db_conn.commit()
                raise SubscriberException('PG_HLR Subscriber not found')
            if prev_status[0] == 0 and status == 1:
                cur.execute(
                    'UPDATE subscribers SET subscription_status = %(status)s, subscription_date = NOW() WHERE msisdn = %(msisdn)s',
                    {'status': status, 'msisdn': msisdn}
                )
            else:
                cur.execute(
                    'UPDATE subscribers SET subscription_status = %(status)s WHERE msisdn=%(msisdn)s',
                    {'status': status, 'msisdn': msisdn}
                )
            if cur.rowcount > 0:
                self._local_db_conn.commit()
            else:
                self._local_db_conn.commit()
                raise SubscriberException('PG_HLR Subscriber not found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error changing subscriber subscription status: %s' % e)

    def edit(self, msisdn, name, balance, location, equipment, roaming):
        params = locals()
        updating = [k for k, v in params.items() if v != ""]
        updating.remove('self')
        updating.remove('msisdn')
        # edit subscriber data in the Osmo
        try:
            appstring = 'OpenBSC'
            appport = 4242
            vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
            cmd = 'enable'
            vty.command(cmd)
            cmd = 'subscriber extension %s name %s' % (msisdn, name)
            vty.command(cmd)
        except Exception as e:
            raise SubscriberException('VTY error updating subscriber data: %s' % e.args[0])
        
        # PG_HLR update subscriber data
        try:
            _set = {}
            for i in updating:
                _set[i] = params[i]
            cur = self._local_db_conn.cursor()
            sql_template = "UPDATE subscribers SET ({}) = %s WHERE msisdn = '{}'"
            sql = sql_template.format(', '.join(_set.keys()), msisdn)
            params = (tuple(_set.values()),)
            cur.execute(sql, params)
            if cur.rowcount > 0:
                self._local_db_conn.commit()
            else:
                self._local_db_conn.commit()
                raise SubscriberException('PG_HLR No subscriber found')
        except psycopg2.DatabaseError as e:
            cur.execute("rollback")
            raise SubscriberException('PG_HLR error updating subscriber data: %s' % e)

    def _get_imsi(self, msisdn):
        try:
            sq_hlr = sqlite3.connect(self._hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('SELECT extension,imsi from subscriber WHERE extension=?', [(msisdn)])
            extension = sq_hlr_cursor.fetchone()
            if  extension == None:
                raise SubscriberException('Extension not found in the OsmoHLR')
            imsi = extension[1]
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])
        return str(imsi)

    def _authorize_subscriber_in_local_hlr(self, msisdn, new_msisdn, name):
        try:
            api_log.debug('Auth Subscriber in Local HLR: %s, %s' % (msisdn, new_msisdn) )
            appstring = 'OpenBSC'
            appport = 4242
            vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
            cmd = 'enable'
            vty.command(cmd)
            cmd = 'subscriber extension %s extension %s' % (msisdn, new_msisdn)
            ret=vty.command(cmd)
            api_log.debug('VTY: %s' % ret)
            cmd = 'subscriber extension %s authorized 1' % new_msisdn
            vty.command(cmd)
            cmd = 'subscriber extension %s name %s' % (new_msisdn, unidecode(name))
            vty.command(cmd)
        except Exception as e:
            raise SubscriberException('SQ_HLR error provisioning the subscriber %s' % e)

    def _provision_in_database(self, msisdn, name, balance, location='', equipment=''):
        try:
            cur = self._local_db_conn.cursor()
            cur.execute(
                'INSERT INTO subscribers(msisdn,name,authorized,balance,subscription_status, '
                'location, equipment) '
                'VALUES(%(msisdn)s,%(name)s,1,%(balance)s,1,%(location)s,%(equipment)s)',
                {
                    'msisdn': msisdn,
                    'name': unidecode(name),
                    'balance': Decimal(str(balance)),
                    'location': location,
                    'equipment': equipment
                }
            )
            cur.execute(
                'INSERT INTO hlr(msisdn, home_bts, current_bts, authorized, updated) VALUES(%(msisdn)s, %(home_bts)s, %(current_bts)s, 1, now())',
                {
                    'msisdn': msisdn,
                    'home_bts': config['local_ip'],
                    'current_bts': config['local_ip']
                }
            )
            self._local_db_conn.commit()
        except psycopg2.DatabaseError as e:
            self._local_db_conn.rollback()
            raise SubscriberException('PG_HLR error provisioning the subscriber: %s' % e)

    def _provision_in_distributed_hlr(self, imsi, msisdn):
        try:
            now = int(time.time())
            rk_hlr = self._riak_client.bucket('hlr')
            distributed_hlr = rk_hlr.new(imsi, data={"msisdn": msisdn, "home_bts": config['local_ip'], "current_bts": config['local_ip'], "authorized": 1, "updated": now})
            distributed_hlr.add_index('msisdn_bin', msisdn)
            distributed_hlr.add_index('modified_int', now)
            distributed_hlr.store()
        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')

    def _delete_in_distributed_hlr(self, msisdn):
        try:
            rk_hlr = self._riak_client.bucket('hlr')
            subscriber = rk_hlr.get_index('msisdn_bin', msisdn, timeout=self._riak_timeout)
            for key in subscriber.results:
                rk_hlr.get(key).remove_indexes().delete()

        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')

    def delete_in_dhlr_imsi(self, imsi):
        try:
            rk_hlr = self._riak_client.bucket('hlr')
            rk_hlr.delete(str(imsi))
        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')

if __name__ == '__main__':
    sub = Subscriber()
    try:
        subs = sub.get_all_roaming()
        print(subs)
    except SubscriberException as e:
        print("Error: %s" % e)
