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

import sys
sys.path.append("..")
from config import *
import obscvty

class SubscriberException(Exception):
    pass

class Subscriber:

    def get_balance(self, subscriber_number):
        # check if extension if yes add internal_prefix
        if len(subscriber_number) == 5:
            subscriber_number = config['internal_prefix']+subscriber_number

        try:
            cur = db_conn.cursor()
            cur.execute("SELECT balance FROM subscribers WHERE msisdn=%(number)s AND authorized=1", {'number': subscriber_number})
            balance = cur.fetchone()
            if balance != None:
                return balance[0]
            else:
                raise SubscriberException("Error in getting subscriber balance")
        except psycopg2.DatabaseError, e:
            raise SubscriberException('Database error in getting subscriber balance: %s' % e)

    def set_balance(self, subscriber_number, balance):
        # check if extension if yes add internal_prefix
        if len(subscriber_number) == 5:
            subscriber_number = config['internal_prefix']+subscriber_number
        try:
            cur = db_conn.cursor()
            cur.execute("UPDATE subscribers SET balance=%(balance)s WHERE msisdn=%(number)s", {'balance': Decimal(str(balance)), 'number': subscriber_number})
            db_conn.commit()
        except psycopg2.DatabaseError, e:
            raise SubscriberException('Database error updating balance: %s' % e)


    def is_authorized(self, subscriber_number, auth_type):
        # auth type 0 check subscriber without checking extension
        # auth type 1 check subscriber with checking extension
        try:
            cur = db_conn.cursor()

            if auth_type == 1:
                # check if extension if yes add internal_prefix used to find the subscriber by the extension
                if len(subscriber_number) == 5:
                    subscriber_number = config['internal_prefix']+subscriber_number

            cur.execute("SELECT msisdn FROM subscribers WHERE msisdn=%(number)s AND authorized=1", {'number': subscriber_number})
            sub = cur.fetchone()
            if sub != None:
                return True
            else:
                return False
        except psycopg2.DatabaseError, e:
            raise SubscriberException('Database error in checking subscriber authorization: %s' % e)

    def get_local_msisdn(self, imsi):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension from subscriber where imsi=%(imsi)s and lac > 0" % {'imsi': imsi})
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
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension from subscriber where imsi=%(imsi)s" % {'imsi': imsi})
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


    def get_all(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM subscribers')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_notpaid(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM subscribers WHERE subscription_status = 0')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_unauthorized(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM subscribers WHERE authorized = 0')
            if cur.rowcount > 0:
                sub = cur.fetchall()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscribers found')
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_all_5digits(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select id, extension from subscriber where length(extension) = 5 AND extension != ?", [(config['smsc'])])
            extensions = sq_hlr_cursor.fetchall()
            if extensions == []:
                raise SubscriberException('No extensions found')
            else:
                sq_hlr.close()
                return extensions
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])


    def get_all_connected(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension from subscriber where extension like ? and lac > 0", [(config['internal_prefix']+'%')])
            connected = sq_hlr_cursor.fetchall()
            if connected == []:
                raise SubscriberException('No connected subscribers found')
            else:
                sq_hlr.close()
                return connected

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_unregistered(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension,imsi from subscriber where length(extension) = 5 and lac > 0")
            unregistered = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return unregistered

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_foreign(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension,imsi from subscriber where length(extension) = 11 and extension not like '%s%%' and lac > 0" % config['internal_prefix'])
            foreign = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return foreign
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_since(self, days):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension from subscriber where (length(extension) = 5 or extension not like \"%(prefix)s%%\") and extension != %(smsc)s and updated < date('now', '-%(days)s days')" % {'days': days, 'smsc': config['smsc'], 'prefix': config['internal_prefix']})
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive

        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_roaming(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select extension from subscriber where length(extension) = 11 and extension not like '%s%%' and lac = 0" % config['internal_prefix'])
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_all_roaming(self):
        try:
            results = riak_client.add('hlr').map(
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
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select count(*) from subscriber where length(extension) = 11 and lac > 0")
            connected = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return connected[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_offline(self):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select count(*) from subscriber where length(extension) = 11 and lac = 0")
            offline = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            return offline[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

    def get_unpaid_subscription(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers WHERE subscription_status=0')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_paid_subscription(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers WHERE subscription_status=1')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get_unauthorized(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT count(*) FROM subscribers WHERE authorized=0')
            sub = cur.fetchone()
            return sub[0]
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting subscribers: %s' % e)

    def get(self, msisdn):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM subscribers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
                sub = cur.fetchone()
                return sub
            else:
                raise SubscriberException('PG_HLR No subscriber found')
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error getting subscriber: %s' % e)

    def set_lac(self, imsi, lac):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            print 'Update lac %s %s' % (imsi, lac)
            sq_hlr_cursor.execute('UPDATE subscriber set lac=? where imsi=?', [(imsi, lac)])
            sq_hlr.commit()
            sq_hlr_cursor.execute('UPDATE subscriber set lac=? where imsi=?', [(imsi, lac)])
            sq_hlr.commit()
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error updating subscriber lac: %s' % e.args[0])

    def add(self, msisdn, name, balance, location=''):
        if len(msisdn) == 15:
            # lookup extension by imsi
            extension = self.get_local_extension(msisdn)
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
                self._provision_in_database(subscriber_number, name, balance, location)
            except SubscriberException as e:
                # revert back the change on SQ_HLR
                self._authorize_subscriber_in_local_hlr(subscriber_number, msisdn, name)
                raise SubscriberException('Error provisioning new number %s, please try again. ERROR: %s' % (msisdn, str(e)))
        else:
            try:
                self._authorize_subscriber_in_local_hlr(msisdn, subscriber_number, name)
                self._provision_in_database(subscriber_number, name, balance, location)
            except SubscriberException as e:
                # revert back the change on SQ_HLR
                self._authorize_subscriber_in_local_hlr(subscriber_number, msisdn, name)
                raise SubscriberException('Error provisioning the number %s, please try again. ERROR: %s' % (msisdn, str(e)))
                
        return msisdn

    def _check_subscriber_exists(self, msisdn):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('SELECT extension FROM subscriber where extension=?', [(config['internal_prefix'] + msisdn)])
            entry = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if len(entry) <= 0:
                return False
            return True
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error sub: %s' % e.args[0])

    def _get_new_msisdn(self, msisdn, name):
        try:
            while True:
                # if last ext available reset to 0
                if msisdn == 99999:
                    msisdn = 00000
                # increment msisdn of one and check if exists
                newexti = int(msisdn) + 1
                newext = str(newexti)
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
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get(str(imsi), timeout=RIAK_TIMEOUT)
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
            cur = db_conn.cursor()
            update_date = datetime.datetime.fromtimestamp(subscriber.data['updated'])
            cur.execute('UPDATE hlr SET msisdn=%(msisdn)s, home_bts=%(home_bts)s, current_bts=%(current_bts)s, '
                        'authorized=%(authorized)s, updated=%(updated)s WHERE msisdn=%(msisdn)s',
            {'msisdn': subscriber.data['msisdn'], 'home_bts': subscriber.data['home_bts'], 'current_bts': subscriber.data['current_bts'],
            'authorized': subscriber.data['authorized'], 'updated': update_date})
            db_conn.commit()
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
            cur = db_conn.cursor()
            cur.execute('DELETE FROM subscribers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
            cur.execute('DELETE FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
               db_conn.commit()
        except psycopg2.DatabaseError as e:
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

    def authorized(self, msisdn, auth):
        # auth 0 subscriber disabled
        # auth 1 subscriber enabled
        # disable/enable subscriber on the HLR sqlite DB
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('UPDATE Subscriber SET authorized=? WHERE extension=?', (auth, msisdn))
            if sq_hlr_cursor.rowcount > 0:
                sq_hlr.commit()
            else:
                raise SubscriberException('SQ_HLR Subscriber not found')
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error changing auth status: %s' % e.args[0])
        finally:
            sq_hlr.close()

        # disable/enable subscriber on PG_HLR
        try:
            cur = db_conn.cursor()
            cur.execute('UPDATE subscribers SET authorized=%(auth)s WHERE msisdn=%(msisdn)s', {'auth': auth, 'msisdn': msisdn})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                db_conn.rollback()
                raise SubscriberException('PG_HLR Subscriber not found')
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise SubscriberException('PG_HLR error changing auth status: %s' % e)

        #try:
        #    now = int(time.time())
        #    rk_hlr = riak_client.bucket('hlr')
        #    subscriber = rk_hlr.get_index('msisdn_bin', msisdn, timeout=RIAK_TIMEOUT)
        #    if len(subscriber.results) != 0:
        #        subscriber = rk_hlr.get(subscriber.results[0], timeout=RIAK_TIMEOUT)
        #        subscriber.data['authorized'] = auth
        #        subscriber.data['updated'] = now
        #        subscriber.indexes = set([('modified_int', now), ('msisdn_bin', subscriber.data['msisdn'])])
        #        subscriber.store()
        #    else:
        #        raise NumberingException('RK_DB subscriber %s not found' % msisdn)

        #except riak.RiakError as e:
        #    raise SubscriberException('RK_HLR error: %s' % e)
        #except socket.error:
        #    raise SubscriberException('RK_HLR error: unable to connect')



    def subscription(self, msisdn, status):
        # status 0 - subscription not paid
        # status 1 - subscription paid
        try:
            cur = db_conn.cursor()
            cur.execute('UPDATE subscribers SET subscription_status=%(status)s WHERE msisdn=%(msisdn)s', {'status': status, 'msisdn': msisdn})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                raise SubscriberException('PG_HLR Subscriber not found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error changing subscriber subscription status: %s' % e)



    def edit(self, msisdn, name, balance, location):
        # edit subscriber data in the SQ_HLR
        #try:
        #   sq_hlr = sqlite3.connect(sq_hlr_path)
        #   sq_hlr_cursor = sq_hlr.cursor()
        #   sq_hlr_cursor.execute('UPDATE Subscriber set extension=?,name=? where extension=?', (msisdn, name, msisdn))
        #   if sq_hlr_cursor.rowcount > 0:
        #       sq_hlr.commit()
        #   else:
        #       raise SubscriberException('SQ_HLR No subscriber found')
        #except sqlite3.Error as e:
        #   raise SubscriberException('SQ_HLR error updating subscriber data: %s' % e.args[0])
        #finally:
        #   sq_hlr.close()

        # PG_HLR update subscriber data
        try:
            cur = db_conn.cursor()
            if balance != "":
		if location != "":
	                cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s,balance=%(balance)s,location=%(location)s WHERE msisdn=%(msisdn2)s',
        	        {'msisdn': msisdn, 'name': name, 'balance': Decimal(str(balance)), 'msisdn2': msisdn, 'location': location})
		else:
	                cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s,balance=%(balance)s WHERE msisdn=%(msisdn2)s',
        	        {'msisdn': msisdn, 'name': name, 'balance': Decimal(str(balance)), 'msisdn2': msisdn})

            else:
		if location != "":
	                cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s,location=%(location)s WHERE msisdn=%(msisdn2)s',
        	        {'msisdn': msisdn, 'name': name, 'msisdn2': msisdn, 'location': location})
		else:
	                cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s WHERE msisdn=%(msisdn2)s',
        	        {'msisdn': msisdn, 'name': name, 'msisdn2': msisdn})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                raise SubscriberException('PG_HLR No subscriber found')
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error updating subscriber data: %s' % e)

    def _get_imsi(self, msisdn):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('select extension,imsi from subscriber where extension=?', [(msisdn)])
            extension = sq_hlr_cursor.fetchone()
            if  extension == None:
                raise SubscriberException('Extension not found in the HLR')
            imsi = extension[1]
        except sqlite3.Error as e:
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])
        return str(imsi)

    def _authorize_subscriber_in_local_hlr(self, msisdn, new_msisdn, name):
        try:
            appstring = 'OpenBSC'
            appport = 4242
            vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
            cmd = 'enable'
            vty.command(cmd)
            cmd = 'subscriber extension %s extension %s' % (msisdn, new_msisdn)
            vty.command(cmd)
            cmd = 'subscriber extension %s authorized 1' % new_msisdn
            vty.command(cmd)
            cmd = 'subscriber extension %s name %s' % (new_msisdn, unidecode(name))
            vty.command(cmd)
        except:
            raise SubscriberException('SQ_HLR error provisioning the subscriber')

    def _provision_in_database(self, msisdn, name, balance, location=''):
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO subscribers(msisdn,name,authorized,balance,subscription_status,location) VALUES(%(msisdn)s,%(name)s,1,%(balance)s,1,%(location)s)',
            {'msisdn': msisdn, 'name': unidecode(name), 'balance': Decimal(str(balance)), 'location': location})
            cur.execute('INSERT INTO hlr(msisdn, home_bts, current_bts, authorized, updated) VALUES(%(msisdn)s, %(home_bts)s, %(current_bts)s, 1, now())',
            {'msisdn': msisdn, 'home_bts': config['local_ip'], 'current_bts': config['local_ip']})
            db_conn.commit()
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise SubscriberException('PG_HLR error provisioning the subscriber: %s' % e)

    def _provision_in_distributed_hlr(self, imsi, msisdn):
        try:
            now = int(time.time())
            rk_hlr = riak_client.bucket('hlr')
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
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get_index('msisdn_bin', msisdn, timeout=RIAK_TIMEOUT)
            for key in subscriber.results:
                rk_hlr.get(key).delete()

        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)
        except socket.error:
            raise SubscriberException('RK_HLR error: unable to connect')


if __name__ == '__main__':
    sub = Subscriber()
    try:
	subs = sub.get_all_roaming()
	print subs
    except SubscriberException as e:
        print "Error: %s" % e
