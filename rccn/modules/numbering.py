############################################################################
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Numbering module
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
from ESL import *

class NumberingException(Exception):
    pass

class Numbering:
    
    def is_number_sip_connected(self, session, number):
        try:
            session.execute('set', "sofia_contact_=${sofia_contact("+number+")}")
            _sofia_contact=session.getVariable("sofia_contact_")
            if _sofia_contact == 'error/user_not_registered':
                session.execute('set', "sofia_contact_=${sofia_contact(*/"+number+"@"+wan_ip_address+")}")
                _sofia_contact=session.getVariable("sofia_contact_")
            log.info('Sofia Contact: %s' % _sofia_contact)
            if _sofia_contact == '' or _sofia_contact == 'error/user_not_registered':
                return False
            return _sofia_contact
        except Exception as ex:
            log.info('Exception: %s' % ex)

    def is_number_sip_connected_no_session(self, number):
        # Carefult with this, seems to lock up FS console if called from chatplan.
        # That is to say, don't connect back via ESL from the chatplan.
        try:
            con = ESLconnection("127.0.0.1", "8021", "ClueCon")
            e = con.api("sofia_contact "+str(number))
            _sofia_contact=e.getBody()
            if _sofia_contact == 'error/user_not_registered':
                e = con.api( "sofia_contact */" + str(number) + "@" + str(wan_ip_address) )
                _sofia_contact=e.getBody()
            log.info('Sofia Contact: %s' % _sofia_contact)
            if _sofia_contact == '' or _sofia_contact == 'error/user_not_registered':
                return False
            return _sofia_contact
        except Exception as ex:
            log.info('Exception: %s' % ex)

    def is_number_did(self, destination_number):
        try:
            cur = db_conn.cursor()
            cur.execute("SELECT phonenumber FROM dids WHERE phonenumber=%(number)s", {'number': destination_number})
            did = cur.fetchone()
            #log.debug("Value of did var: %s" % did)
            if did != None:
                return True
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error checking DID: %s' % e)

    def fivetoeleven(self, source_number, destination_number):
        """ Convert a five digit extension to 11 digits based on the caller. """
        if len(destination_number) !=5:
            return destination_number
        return source_number[:6] + destination_number

    def is_number_local(self, destination_number):
        # check if extension if yes add internal_prefix
        if len(destination_number) == 5:
            destination_number = config['internal_prefix'] + destination_number

        try:
            cur = db_conn.cursor()
            cur.execute('SELECT msisdn FROM subscribers WHERE msisdn=%(number)s', {'number': destination_number})
            dest = cur.fetchone()
            if dest != None:
                destn = dest[0]
                # check if number is local to the site
                if destn[:6] == config['internal_prefix']:
                    return True
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error checking if number is local:' % e )


    def is_number_internal(self, destination_number):
        siteprefix = destination_number[:6]
        if siteprefix == config['internal_prefix']:
            return False
        # Try to avoid going to RIAK here
        cur = db_conn.cursor()
        cur.execute('SELECT DISTINCT home_bts FROM hlr WHERE msisdn like %(prefix)s', {'prefix': siteprefix+'%'})
        test = cur.fetchall()
        if len(test) > 1:
            log.warn('!!FIX THIS!! Got more than one home_bts from hlr for %s' % siteprefix)
            sites = riak_client.bucket('sites')
            if sites.get(siteprefix).exists == True:
                return True
            else:
                return False
        elif len(test) == 1:
            return True
        else:
            return False

    def is_number_here(self, number):
        log.info('%s %s %s %s' % (self.calling_host,mncc_ip_address,number[:6],config['internal_prefix']))
        if self.calling_host == mncc_ip_address and number[:6] == config['internal_prefix']:
            # If we are here and are a local number, then we can't be roaming
            log.warn('%s is here' % number)
            return False

    def is_number_roaming(self, number):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            subscriber = cur.fetchone()
            if subscriber != None:
                if subscriber['home_bts'] != subscriber['current_bts']:
                    if subscriber['authorized'] == 1:
                        return True
                    else:
                        raise NumberingException('RK_DB subscriber %s is roaming on %s but is not authorized' % (number, subscriber['current_bts']))
            return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('PG_HLR error checking if number is in roaming:' % e)

    def get_dhlr_entry(self,imsi):
        try:
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get(str(imsi), timeout=RIAK_TIMEOUT)
            if not subscriber.exists:
                raise NumberingException('RK_HLR imsi %s not found' % imsi)
            return subscriber.data
        except riak.RiakError as e:
            raise NumberingException('RK_HLR error getting the msisdn from an imsi: %s' % e)
        except socket.error:
            raise NumberingException('RK_HLR error: unable to connect')

    def get_msisdn_from_imsi(self, imsi):
        try:
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get(str(imsi), timeout=RIAK_TIMEOUT)
            if not subscriber.exists:
                raise NumberingException('RK_DB imsi %s not found' % imsi)
            if subscriber.data["authorized"] != 1:
                raise NumberingException('RK_DB imsi %s (%s) not authorized' % (imsi, subscriber.data['msisdn']))
            return subscriber.data["msisdn"]

        except riak.RiakError as e:
            raise NumberingException('RK_HLR error getting the msisdn from an imsi: %s' % e)
        except socket.error:
            raise NumberingException('RK_HLR error: unable to connect')

    def get_msisdn_from_imei(self, imei):
        try:
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql=('SELECT Equipment.imei, Subscriber.imsi, '
            'Subscriber.extension, Subscriber.updated '
            'FROM Equipment, EquipmentWatch, Subscriber '
            'WHERE EquipmentWatch.equipment_id=Equipment.id '
            'AND EquipmentWatch.subscriber_id=Subscriber.id '
            'AND Equipment.imei=? '
            'ORDER BY Subscriber.updated DESC LIMIT 1;')
            print sql
            sq_hlr_cursor.execute(sql, [(imei)])
            extensions = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return extensions
        except sqlite3.Error as e:
            sq_hlr.close()
            raise NumberingException('SQ_HLR error: %s' % e.args[0])

    def get_imei_autocomplete(self, partial_imei=''):
        try: 
            sq_hlr = sqlite3.connect(sq_hlr_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql='SELECT DISTINCT Equipment.imei FROM Equipment '
            if partial_imei!='':
                sql+='WHERE Equipment.imei LIKE ? ORDER BY Equipment.imei ASC'
                sq_hlr_cursor.execute(sql, [(partial_imei+'%')])
            else:
                sq_hlr_cursor.execute(sql)
            imeis = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if imeis == []:
                return []
            if len(imeis)==1:
                data=self.get_msisdn_from_imei(imeis[0][0])
                return data
            else:
                return imeis
        except sqlite3.Error as e:
            sq_hlr.close()
            raise NumberingException('SQ_HLR error: %s' % e.args[0])

    def get_local_hlr_btsinfo(self, number):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT home_bts,current_bts FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            subscriber = cur.fetchone()
            if subscriber != None:
                return subscriber
            else:
                raise NumberingException('PG_DB subscriber not found: %s' % number)
            return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('PG_HLR error getting bts info for:' % e)


    def get_current_bts(self, number):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT current_bts FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            subscriber = cur.fetchone()
            if subscriber != None:
                return subscriber['current_bts']
            else:
                raise NumberingException('PG_DB subscriber not found: %s' % number)
            return False

        except psycopg2.DatabaseError as e:
            raise NumberingException('PG_HLR error checking if number is in roaming:' % e)


    def get_bts_distributed_hlr(self, imsi, bts):
        try:
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get(imsi, timeout=RIAK_TIMEOUT)
            return subscriber.data[bts]
        except riak.RiakError as e:
            raise SubscriberException('RK_HLR error: %s' % e)


    def get_site_ip(self, destination_number):
        siteprefix = destination_number[:6]
        site = riak_client.bucket('sites')
        site_data = site.get(siteprefix)
        if site_data.data['ip_address'] != None:
            return site_data.data['ip_address']
        else:
            raise NumberingException('RK_DB Error no IP found for site %s' % site)

    def get_callerid(self, caller, callee):
        try:
            cur = db_conn.cursor()
            # to still be decided the logic of dids
            if callee[0] == '+':
                dest = callee[1:2]
            if re.search(r'^00', callee) != None:
                dest = callee[2:3]
            cur.execute('select callerid from dids,providers where callerid like %(prefix)s limit 1', {'prefix': '+'+dest+'%'} )
            callerid = cur.fetchone()
            if callerid == None:
                cur.execute('select callerid from dids,providers where providers.id = dids.provider_id and providers.active = 1 order by dids.id asc limit 1')
                callerid = cur.fetchone()
            if callerid != None:
                return callerid[0]
            else:
                return None
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error getting CallerID: %s' % e)

    def get_did_subscriber(self, destination_number):
        try:
            cur = db_conn.cursor()
            cur.execute('select subscriber_number from dids where phonenumber=%(number)s', {'number': destination_number})
            dest = cur.fetchone()
            if dest != None:
                return dest[0]
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error getting subscriber number associated to the DID: %s' % e)

    def get_gateway(self):
        try:
            cur = db_conn.cursor()
            cur.execute('select provider_name from providers where active = 1')
            gw = cur.fetchone()
            if gw != None:
                return gw[0]
            else:
                return None
        except psycopg2.DatabaseError, e:
            raise NumberingException('Database error getting the Gateway: %s' % e)

    def is_number_mxcel(self,number):
        try:
            if len(number) != 10:
                log.debug("Number %s length not 10" % number)
                return False
            number = '521'+number
            cur = db_conn.cursor()
            cur.execute("""SELECT d::text as d FROM prefix_mexico
                WHERE length(d::text) > 6 ORDER BY length(d::text) DESC
                """)
            prefixes = cur.fetchall()
            for prefix in prefixes:
                if number.startswith(prefix[0]):
                    return True
            return False
        except psycopg2.DatabaseError, e:
            db_conn.rollback()
            raise NumberingException('Database error getting the Number Type: %s' % e)

if __name__ == '__main__':
	num = Numbering()
	num.is_number_roaming('66666139666')
