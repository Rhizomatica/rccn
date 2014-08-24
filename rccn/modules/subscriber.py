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

    def is_online(self, subscriber_number):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("select msisdn from subscriber where msisdn=%(number)s and lac > 0", {'number': subscriber_number})
            connected = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return len(connected) > 0
        except sqlite3.Error as e:
            sq_hlr.close()
            raise SubscriberException('SQ_HLR error: %s' % e.args[0])

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

    def get_all_roaming(self):
        results = riak_client.add('hlr').map(
            """
            function(value, keyData, arg) {
                 var data = Riak.mapValuesJson(value)[0];
                 if ((data.home_bts == %s) &&
                     (data.current_bts != data.home_bts))
                   return [value.key];
                 else
                   return [];
            }
            """ % config['local_ip']
            ).run()
        # return [(msisdn, imsi)]
	if results:
            return [(r[1][0], r[0]) for r in results]
	else:
            return []

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

    def add(self, msisdn, name, balance):
        imsi = self._get_imsi(msisdn)
        subscriber_number = config['internal_prefix'] + msisdn

        self._authorize_subscriber_in_local_hlr(msisdn, subscriber_number, name)
        self._provision_in_database(subscriber_number, name, balance)
        self._provision_in_distributed_hlr(imsi, subscriber_number)

    def update(self, msisdn, name, number):
        imsi = self._get_imsi(msisdn)
        self._authorize_subscriber_in_local_hlr(msisdn, number, name)
        self.update_location(imsi, number)

    def update_location(self, imsi, msisdn):
        rk_hlr = riak_client.bucket('hlr')
        subscriber = rk_hlr.get(str(imsi))
        subscriber.data["current_bts"] = config['local_ip']
        subscriber.store()

    def delete(self, msisdn):
        imsi = self._get_imsi(msisdn)

        subscriber_number = msisdn[-5:]
        appstring = 'OpenBSC'
        appport = 4242
        vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
        cmd = 'enable'
        vty.command(cmd)
        cmd = 'subscriber extension %s extension %s' % (msisdn, subscriber_number)
        vty.command(cmd)

        # PG_HLR delete subscriber 
        try:
            cur = db_conn.cursor()
            cur.execute('DELETE FROM subscribers WHERE msisdn=%(msisdn)s', {'msisdn': msisdn})
            if cur.rowcount > 0:
                db_conn.commit()
            else:
                raise SubscriberException('PG_HLR No subscriber found') 
        except psycopg2.DatabaseError, e:
            raise SubscriberException('PG_HLR error deleting subscriber: %s' % e)

        self._delete_in_distributed_hlr(imsi)

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
                raise SubscriberException('PG_HLR Subscriber not found')
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error changing auth status: %s' % e)
            

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



    def edit(self, msisdn, name, balance):
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
                cur.execute('UPDATE subscribers SET msisdn=%(msisdn)s,name=%(name)s,balance=%(balance)s WHERE msisdn=%(msisdn2)s', 
                {'msisdn': msisdn, 'name': name, 'balance': Decimal(str(balance)), 'msisdn2': msisdn})
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
        appstring = 'OpenBSC'
        appport = 4242
        vty = obscvty.VTYInteract(appstring, '127.0.0.1', appport)
        cmd = 'enable'
        vty.command(cmd)
        cmd = 'subscriber extension %s extension %s' % (msisdn, new_msisdn)
        vty.command(cmd)
        cmd = 'subscriber extension %s authorized 1' % new_msisdn
        vty.command(cmd)
        cmd = 'subscriber extension %s name %s' % (new_msisdn, name)
        vty.command(cmd)

    def _provision_in_database(self, msisdn, name, balance):
        try:
            cur = db_conn.cursor()
            cur.execute('INSERT INTO subscribers(msisdn,name,authorized,balance,subscription_status) VALUES(%(msisdn)s,%(name)s,1,%(balance)s,1)', 
            {'msisdn': msisdn, 'name': name, 'balance': Decimal(str(balance))})
            db_conn.commit()
        except psycopg2.DatabaseError as e:
            raise SubscriberException('PG_HLR error provisioning the subscriber: %s' % e)

    def _provision_in_distributed_hlr(self, imsi, msisdn):
        rk_hlr = riak_client.bucket('hlr')
        distributed_hlr = rk_hlr.new(imsi, data={"msisdn": msisdn, "home_bts": config['local_ip'], "current_bts": config['local_ip'], "authorized": 1})
        distributed_hlr.add_index('msisdn_bin', msisdn)
        distributed_hlr.store()

    def _delete_in_distributed_hlr(self, imsi):
        rk_hlr = riak_client.bucket('hlr')
        rk_hlr.get(str(imsi)).delete()


if __name__ == '__main__':
    sub = Subscriber()
    #sub.set_balance('68820110010',3.86)
    try:
        sub.add('20133', 'Test', 0)
	#sub.delete('66666249987')
        #sub.edit('68820137511','Antanz_edit',3.86)
        #sub.authorized('68820137511',0)
        #print sub.get_all_connected()
        
        #a = sub.get('68820137511')
        #print a
        #sub.delete('68820137511')
    except SubscriberException as e:
        print "Error: %s" % e
