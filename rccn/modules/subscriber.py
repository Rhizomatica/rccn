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
import psycopg2
import riak
import socket
import time
from unidecode import unidecode

from config import (db_conn, sq_hlr_path, config, api_log, roaming_log, riak_client, RIAK_TIMEOUT, NoDataException, use_nitb_osmo_stack)
from decimal import Decimal
from modules.osmohlr import (OsmoHlr, OsmoHlrError)
from modules.osmomsc import (OsmoMsc, OsmoMscError)
from modules.osmonitb import (OsmoNitb)
from ESL import ESLconnection

class SubscriberException(Exception):
    pass

class Subscriber:
    """Module encapsulating access to subscriber specific data.
    Args:
        local_db_conn: The connection used for local datastore queries, defaults to the global db_conn
        hlr_ip: The IP address of the network's HLR (home location register)
        hlr_ctrl_port: The port of the HLR's osmo ctrl interface
        hlr_vty_port: The port of the HLR's vty
        hlr_db_path: The path of the sqlite3 database of the hlr, defaults to global config
        msc_ip: The Ip address of the network's MSC (mobile switching center)
        msc_ctrl_port: The port of the msc's osmo ctrl interface
        msc_vty_port: The port of the msc's vty
        riak_client: The riak distributed hlr client, defaults to no riak connection
        riak_timeout: The wait timeout for riak operations
    """

    def __init__(
            self,
            local_db_conn=db_conn,
            hlr_ip="127.0.0.1",
            hlr_ctrl_port=4259,
            hlr_vty_port=4258,
            hlr_db_path=sq_hlr_path,
            msc_ip="127.0.0.1",
            msc_ctrl_port=4255,
            msc_vty_port=4254,
            riak_client=riak_client,
            riak_timeout=RIAK_TIMEOUT
    ):
        self._local_db_conn = local_db_conn
        if use_nitb_osmo_stack:
            # Use the legacy osmocom-nitb adaptor in place of the msc and hlr
            nitb_adaptor_instance = OsmoNitb(hlr_ip, 4242, hlr_db_path)
            self._osmo_hlr = nitb_adaptor_instance
            self._osmo_msc = nitb_adaptor_instance
        else:
            self._osmo_hlr = OsmoHlr(hlr_ip, hlr_ctrl_port, hlr_vty_port, hlr_db_path)
            self._osmo_msc = OsmoMsc(msc_ip, msc_ctrl_port, msc_vty_port)
        self._riak_client = riak_client
        self._riak_timeout = riak_timeout

    def get_balance(self, subscriber_number):
        # check if extension if yes add internal_prefix
        if len(subscriber_number) == 5:
            subscriber_number = config['internal_prefix']+subscriber_number

        cur = self._open_local_cursor()

        try:
            cur.execute("SELECT balance FROM subscribers WHERE msisdn = %(number)s AND authorized=1", {'number': subscriber_number})
            balance = cur.fetchone()
            if balance != None:
                return balance[0]
            else:
                raise SubscriberException("Error in getting subscriber balance")
        except psycopg2.DatabaseError as e:
            raise SubscriberException('Database error in getting subscriber balance: %s' % e)
        finally:
            cur.close()

    def set_balance(self, subscriber_number, balance):
        # check if extension if yes add internal_prefix
        if len(subscriber_number) == 5:
            subscriber_number = config['internal_prefix']+subscriber_number

        cur = self._open_local_cursor()

        try:
            cur.execute("UPDATE subscribers SET balance = %(balance)s WHERE msisdn = %(number)s", {'balance': Decimal(str(balance)), 'number': subscriber_number})
            self._local_db_conn.commit()
        except psycopg2.DatabaseError as e:
            raise SubscriberException('Database error updating balance: %s' % e)
        finally:
            cur.close()


    def is_authorized(self, subscriber_number, auth_type):
        # auth type 0 check subscriber without checking extension
        # auth type 1 check subscriber with checking extension
        cur = self._open_local_cursor()

        try:
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
        finally:
            cur.close()

    def get_local_msisdn(self, imsi):
        # TODO(matt9j) Check for duplication
        try:
            return self._osmo_hlr.get_local_msisdn(imsi)
        except OsmoHlrError as e:
            raise SubscriberException("OsmoHlr error: {}".format(e.args[0]))

    def get_local_extension(self, imsi):
        # TODO(matt9j) Check for duplication
        try:
            return self._osmo_hlr.get_msisdn_from_imsi(imsi)
        except OsmoHlrError as e:
            raise SubscriberException("OsmoHlr error: {}".format(e.args[0]))

    def get_msisdn_from_imei(self, imei):
        try:
            return self._osmo_hlr.get_msisdn_from_imei(imei)
        except OsmoHlrError as e:
            raise SubscriberException("OsmoHlr error: {}".format(e.args[0]))

    def get_imei_autocomplete(self, partial_imei=''):
        try:
            if partial_imei != '':
                imeis = self._osmo_hlr.get_matching_partial_imeis(partial_imei)
            else:
                imeis = self._osmo_hlr.get_all_imeis()

            if len(imeis) == 0:
                return []
            if len(imeis) == 1:
                data = self._osmo_hlr.get_msisdn_from_imei(imeis[0][0])
                return data
            else:
                return imeis
        except OsmoHlrError as e:
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all(self):
        cur = self._open_local_cursor()
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT * FROM subscribers')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
        finally:
            cur.close()

    def get_all_notpaid(self, location=False):
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

    def get_all_authorized(self, location=False):
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

    def get_all_unauthorized(self, location=False):
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

    def get_all_5digits(self):
        try:
            msisdns = self._osmo_hlr.get_all_5digit_msisdns()
            results = []
            for msisdn_tuple in msisdns:
                if msisdn_tuple[1] != config['smsc']:
                    results.append(msisdn_tuple)

            if len(msisdns) == 0:
                raise NoDataException('No extensions found')
            else:
                return results
        except OsmoHlrError as e:
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_expire(self):
        try:
            updates = self._osmo_hlr.get_all_expire()
            if len(updates) == 0:
                raise SubscriberException('No subscribers found')
            return updates
        except OsmoHlrError as e:
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
            connected_subs = self._osmo_msc.get_active_subscribers()
            if len(connected_subs) == 0:
                raise SubscriberException('No connected subscribers found')

            # Reformat to msisdn list for API compatibility
            msisdns = []
            for connected_sub in connected_subs:
                if (connected_sub["msisdn"][:6] == config['internal_prefix']):
                    # The RAI PhP code expects a doubly nested array. See
                    # rai/modules/subscriber.php:113
                    msisdns.append([connected_sub["msisdn"]])

            return msisdns
        except OsmoMscError as e:
            raise SubscriberException('MSC error: %s' % e.args[0])

    def get_all_disconnected(self):
        """
        This function used to do a SELECT on the osmo subscriber table with
        WHERE conditions for matching the local_prefix and lac = 0.
        This reimplementation for split stack is not /quite/ the same thing. Now we get
        the list of registered subs on the postgres and remove the MSCs idea of what is
        connected. All the same, the function appears to be unused.
        """
        cur = self._open_local_cursor()
        try:
            cur.execute('SELECT msisdn FROM subscribers')
            subs = cur.fetchall()
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
        finally:
            cur.close()

        try:
            connected_subs = self._osmo_msc.get_active_subscribers()
        except OsmoMscError as e:
            raise SubscriberException('MSC error: %s' % e.args[0])

        # Build a set first for O(1) membership testing used in the loop below
        connected_subs = set(x["msisdn"] for x in connected_subs)

        disconnected = []
        for sub in subs:
            if sub not in connected_subs:
                disconnected.append(sub)

        return disconnected

    def get_all_unregistered(self):
        try:
            connected_subs = self._osmo_msc.get_active_subscribers()

            # Reformat to msisdn list and only include 5 digit numbers for API compatibility
            # An automatically assigned 5 digit msisdn signals that the subscriber is unregistered
            msisdns = []
            for connected_sub in connected_subs:
                if len(connected_sub["msisdn"]) == 5:
                    msisdns.append([connected_sub["msisdn"], connected_sub["imsi"]])

            return msisdns
        except OsmoMscError as e:
            raise SubscriberException('MSC error: %s' % e.args[0])

    def get_all_foreign(self):
        try:
            connected_subs = self._osmo_msc.get_active_subscribers()

            # Reformat to msisdn list and only include 11 digit numbers with
            # noninternal prefixes for API compatibility.
            msisdns = []
            for connected_sub in connected_subs:
                if ((len(connected_sub["msisdn"]) == 11) and
                    (not connected_sub["msisdn"][:6] == config['internal_prefix'])):
                    msisdns.append([connected_sub["msisdn"], connected_sub["imsi"]])

            return msisdns
        except OsmoMscError as e:
            raise SubscriberException('MSC error: %s' % e.args[0])

    def get_all_inactive_since(self, days):
        try:
            inactive_msisdns = self._osmo_hlr.get_all_inactive_msisdns_since(
                days, config['internal_prefix']
            )

            try:
                inactive_msisdns.remove((config['smsc'],))
            except ValueError:
                # It's okay to fail removal if the value is not present
                pass

            return inactive_msisdns
        except OsmoHlrError as e:
            raise SubscriberException('HLR error: %s' % e.args[0])

    def get_all_inactive_roaming(self):
        """
        This function is not in use.
        """
        try:
            inactive_msisdns = self._osmo_hlr.get_all_inactive_roaming_msisdns(config['internal_prefix'])
        except OsmoHlrError as e:
            raise SubscriberException('HLR error: %s' % e.args[0])

        # The existing code explicitly checked that the subscribers were not
        # attached, by inclusion of a WHERE condition lac=0 in the SQL.
        # The OsmoHlr version of the called function above knows nothing
        # about "inactive", where as for nitb we still have lac = 0 so the following
        # code is not needed.
        # Anyway, this function is unused, but see the _since() version below
        # which will be retired along with riak roaming, which will not be used
        # with Split Stack. Long story short, most of this will be removed.
        try:
            connected_subs = self._osmo_msc.get_active_subscribers()
        except OsmoMscError as e:
            raise SubscriberException("MSC error: {}".format(e.args[0]))

        connected_msisdns = set()
        for connected_sub in connected_subs:
            connected_msisdns.add(connected_sub["msisdn"])

        filtered_result = []
        for (inactive_msisdn,) in inactive_msisdns:
            if inactive_msisdn not in connected_msisdns:
                # Format as a nested list for API compatibility
                filtered_result.append([inactive_msisdn])

        return filtered_result

    def get_all_inactive_roaming_since(self, days):
        try:
            inactive_msisdns = self._osmo_hlr.get_all_inactive_roaming_msisdns_since(days, config['internal_prefix'])
        except OsmoHlrError as e:
            raise SubscriberException('HLR error: %s' % e.args[0])

        # The existing code explicitly checked that the subscribers were not
        # attached, which may not be necessary for nonzero time since inactive.
        try:
            connected_subs = self._osmo_msc.get_active_subscribers()
        except OsmoMscError as e:
            raise SubscriberException("MSC error: {}".format(e.args[0]))

        connected_msisdns = set()
        for connected_sub in connected_subs:
            connected_msisdns.add(connected_sub["msisdn"])

        filtered_result = []
        for (inactive_msisdn,) in inactive_msisdns:
            if inactive_msisdn not in connected_msisdns:
                # Format as a nested list for API compatibility
                filtered_result.append([inactive_msisdn])

        return filtered_result

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
            connected_subs = self._osmo_msc.get_active_subscribers()

            # Only include 11 digit numbers for API compatibility.
            count = 0
            for connected_sub in connected_subs:
                if len(connected_sub["msisdn"]) == 11:
                    count += 1

            return count
        except OsmoMscError as e:
            raise SubscriberException('MSC error: %s' % e.args[0])

    def get_offline(self):
        # There is a race condition here since these values are coming from
        # two different databases (postgres and the MSC) and an update could
        # be in progress while the count is computed.
        cur = self._open_local_cursor()
        try:
            cur = self._local_db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers')
            if cur.rowcount > 0:
                total_subscriber_count = cur.fetchone()[0]
            else:
                raise SubscriberException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
        finally:
            cur.close()

        online_count = self.get_online()

        return total_subscriber_count - online_count

    def get_roaming(self):
        try:
            active_subs = self._osmo_msc.get_active_subscribers()
        except OsmoMscError as e:
            raise SubscriberException("MSC error: {}".format(e.args[0]))

        count = 0
        for sub in active_subs:
            if len(sub["msisdn"]) == 11 and sub["msisdn"][:6] != config['internal_prefix']:
                count += 1

        return count


    def get_unpaid_subscription(self):
        cur = self._open_local_cursor()
        try:
            cur.execute('SELECT count(*) FROM subscribers WHERE subscription_status=0')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
        finally:
            cur.close()

    def get_paid_subscription(self):
        cur = self._open_local_cursor()
        try:
            cur.execute('SELECT count(*) FROM subscribers WHERE subscription_status=1')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
        finally:
            cur.close()

    def get_unauthorized(self):
        cur = self._open_local_cursor()
        try:
            cur.execute('SELECT count(*) FROM subscribers WHERE authorized=0')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)
        finally:
            cur.close()

    def get(self, msisdn):
        cur = self._open_local_cursor()
        try:
            cur.execute('SELECT * FROM subscribers WHERE msisdn = %(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
                sub = cur.fetchone()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscriber found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscriber: %s' % e)
        finally:
            cur.close()

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
        try:
            self._osmo_msc.expire_subscriber_by_msisdn(msisdn)
        except OsmoMscError as e:
            raise SubscriberException("Expire LU exception: {}".format(e))

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
            full_msisdn = config['internal_prefix'] + msisdn
            entry = self._osmo_hlr.get_imsi_from_msisdn(full_msisdn)
            return entry is not None
        except OsmoHlrError as e:
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
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

    def update_location_local_hlr(self, extension, current_bts=False):
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

    def delete(self, msisdn):
        subscriber_number = msisdn[-5:]
        try:
            self._osmo_hlr.update_msisdn(msisdn, subscriber_number)
        except:
            pass

        # PG_HLR delete subscriber
        cur = self._open_local_cursor()
        try:
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
        except psycopg2.DatabaseError as e:
            pass
        finally:
            cur.close()

        self._delete_in_distributed_hlr(msisdn)

    def purge(self, msisdn):
        self._osmo_hlr.delete_by_msisdn(msisdn)

    def print_vty_hlr_info(self, msisdn):
        return self._osmo_hlr.show_by_msisdn(msisdn)
        

    def authorized(self, msisdn, auth):
        # auth 0 subscriber disabled
        # auth 1 subscriber enabled
        if auth == 0:
            self._osmo_hlr.disable_access_by_msisdn(msisdn)
        elif auth == 1:
            self._osmo_hlr.enable_access_by_msisdn(msisdn)
        else:
            raise SubscriberException("Unknown auth mode '{}'".format(auth))

        # disable/enable subscriber on PG Subscribers
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

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
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

    def edit(self, msisdn, name, balance, location, equipment, roaming):
        parameter_set = {
            "name": name,
            "balance": balance,
            "location": location,
            "equipment": equipment,
            "roaming": roaming
        }
        _set = {col: value for col, value in parameter_set.items() if value != ""}

        # PG_HLR update subscriber data
        cur = self._open_local_cursor()
        try:
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
            self._local_db_conn.rollback()
            raise SubscriberException('PG_HLR error updating subscriber data: %s' % e)
        finally:
            cur.close()

    def _get_imsi(self, msisdn):
        try:
            imsi = self._osmo_hlr.get_imsi_from_msisdn(msisdn)
        except OsmoHlrError as e:
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])
        return str(imsi)

    def _authorize_subscriber_in_local_hlr(self, msisdn, new_msisdn, name):
        try:
            api_log.debug('Auth Subscriber in Local HLR: %s, %s' % (msisdn, new_msisdn) )
            self._osmo_hlr.update_msisdn(msisdn, new_msisdn)
            self._osmo_hlr.enable_access_by_msisdn(new_msisdn)
        except Exception as e:
            raise SubscriberException('SQ_HLR error provisioning the subscriber %s' % e)

    def _provision_in_database(self, msisdn, name, balance, location='', equipment=''):
        cur = self._open_local_cursor()
        try:
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
        finally:
            cur.close()

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

    def _open_local_cursor(self):
        """Opens a new cursor to the local DB or raises a SubscriberException
        """
        try:
            return self._local_db_conn.cursor()
        except psycopg2.DatabaseError as err:
            raise SubscriberException("DB connection error {}".format(err))

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
