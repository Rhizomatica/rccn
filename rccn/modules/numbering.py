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

from riak import RiakError

class NumberingException(Exception):
    pass

class Numbering:
    
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

        try:
            sites = riak_client.bucket('sites')
            if sites.get(siteprefix).exists == True:
                return True
            else:
                return False

        except RiakError as e:
            raise NumberingException('RK_HLR error checking if number is internal: %s' % e)

    def is_number_roaming(self, number):
<<<<<<< HEAD
        rk_hlr = riak_client.bucket('hlr')
        subscriber = rk_hlr.get_index('msisdn_bin', number)
        if len(subscriber.results) != 0:
            subscriber = rk_hlr.get(subscriber.results[0])
            if subscriber.data["home_bts"] != subscriber.data["current_bts"]:
                if subscriber.data["authorized"] == 1:
                    return True
                else:
                    raise NumberingException('RK_DB subscriber %s is roaming on %s but is not authorized' % (number, subscriber[2]))
        return False                

    def get_msisdn_from_imsi(self, imsi):
        rk_hlr = riak_client.bucket('hlr')
        subscriber = rk_hlr.get(str(imsi))
        if not subscriber.exists:
            raise NumberingException('RK_DB imsi %s not found' % imsi)
        if subscriber.data["authorized"] != 1:
            raise NumberingException('RK_DB imsi %s (%s) not authorized' % (imsi, subscriber.data['msisdn']))
        return subscriber.data["msisdn"]

    def get_current_bts(self, number):
        rk_hlr = riak_client.bucket('hlr')
        subscriber = rk_hlr.get_index('msisdn_bin', number)
        if len(subscriber.results) != 0:
            subscriber = rk_hlr.get(subscriber.results[0])
            return subscriber.data['current_bts']
        else:
            raise NumberingException('RK_DB subscriber %s not found' % number)
        return False
=======
        try:
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get_index('msisdn_bin', number)
            if subscriber.results != []:
                # user found check if home_bts != current_bts
                if subscriber[1] != subscriber[2]:
                    # subscriber is roaming, check auth
                    if subscriber[3] == 1:
                        return True
                    else:
                        raise NumberingException('RK_HLR subscriber %s is roaming on %s but is not authorized' % (number, subscriber[2]))
            return False                

        except RiakError as e:
            raise NumberingException('RK_HLR error checking if number is in roaming: %s' % e)

    def get_msisdn_from_imsi(self, imsi):
        try:
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get(imsi)
            if subscriber.results == 0:
                raise NumberException('RK_HLR imsi %s not found' % imsi)
            if subscriber[3] != 1:
                raise NumberException('RK_HLR imsi %s (%s) not authorized' % (imsi, subscriber[0]))
            return subscriber[0]

        except RiakError as e:
            raise NumberingException('RK_HLR error getting the msisdn from an imsi: %s' % e)

    def get_current_bts(self, number):
        try:
            rk_hlr = riak_client.bucket('hlr')
            subscriber = rk_hlr.get_index('msisdn_bin', number)
            if subscriber.results != 0:
                return subscriber[2]
            else:
                raise NumberException('RK_HLR subscriber %s not found' % number)
            return False

        except RiakError as e:
            raise NumberingException('RK_HLR error getting the current bts: %s' % e)
>>>>>>> catch_riak_errors

    def get_site_ip(self, destination_number):
        siteprefix = destination_number[:6]
        try:
            site = riak_client.bucket('sites')
            site_data = site.get(siteprefix)
            if site_data.data['ip_address'] != None:
                return site_data.data['ip_address']
            else:
                raise NumberingException('RK_HLR Error no IP found for site %s' % site)

        except RiakError as e:
            raise NumberingException('RK_HLR error getting the site IP: %s' % e)

    def get_callerid(self):
        try:
            cur = db_conn.cursor()
            # to still be decided the logic of dids
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


if __name__ == '__main__':
	num = Numbering()
	num.is_number_roaming('66666139666')
