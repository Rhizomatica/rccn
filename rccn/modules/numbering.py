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

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

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
            _sofia_contact = session.getVariable("sofia_contact_")
            if _sofia_contact == 'error/user_not_registered':
                session.execute('set', "sofia_contact_=${sofia_contact(*/"+number+"@"+wan_ip_address+")}")
                _sofia_contact = session.getVariable("sofia_contact_")
            log.info('Sofia Contact: %s' % _sofia_contact)
            if _sofia_contact == '' or _sofia_contact == 'error/user_not_registered':
                return False
            return _sofia_contact
        except Exception as ex:
            log.info('Exception: %s' % ex)
            return False

    def is_number_sip_connected_no_session(self, number):
        # Carefult with this, seems to lock up FS console if called from chatplan.
        # That is to say, don't connect back via ESL from the chatplan.
        try:
            con = ESLconnection("127.0.0.1", "8021", "ClueCon")
            esl = con.api("sofia_contact "+str(number))
            _sofia_contact = esl.getBody()
            if _sofia_contact == 'error/user_not_registered':
                esl = con.api("sofia_contact */" + str(number) + "@" + str(wan_ip_address))
                _sofia_contact = esl.getBody()
            log.info('Sofia Contact: %s' % _sofia_contact)
            if _sofia_contact == '' or _sofia_contact == 'error/user_not_registered':
                return False
            return _sofia_contact
        except Exception as ex:
            log.info('Exception: %s' % ex)

    def prefixplus(self, callerid):
        ''' If the caller id looks like an international number
            prefix it with a + if that is not already the case.
        '''
        if not len(callerid):
            return ''
        if (callerid[:1] == '+' or callerid[:2] == '00'):
            return callerid
        log.info('Caller ID has no INTL prefix: %s', callerid)
        # TODO: Make this a lookup on valid country codes and lengths?
        # All Mexican numbbers are 10 digits long. and NANP. (?)
        if ((len(callerid) == 11 and callerid[:1] == '1') or
            (len(callerid) == 12 and callerid[:2] == '52') or
            callerid[:2] == '57'):
            return '+' + callerid
        # Otherwise?
        return callerid

    def is_number_intl(self, destination_number):
        if (destination_number[0] == '+' or
                destination_number[:2] == '00'):
            log.debug('Called number has international prefix.')
            return self.is_number_intl_valid(destination_number)
        return False

    def is_number_intl_valid(self,destination_number):

        _match = re.split(r'^(00|\+)(1|52)(1?)(.*)$',
                          destination_number)
        if len(_match) > 4:
            return len(_match[4]) == 10

        '''
        if destination_number[:5] == '00521':
            return len(destination_number[5:]) == 10

        if destination_number[:4] == '0052':
            return len(destination_number[4:]) == 10

        if destination_number[:4] == '+521':
            return len(destination_number[4:]) == 10

        if destination_number[:3] == '+52':
            return len(destination_number[3:]) == 10

        if destination_number[:3] == '001':
            return len(destination_number[3:]) == 10

        if destination_number[:2] == '+1':
            return len(destination_number[2:]) == 10
        '''
        return True

    def detect_mx_short_dial(self, destination_number):
        """
        Try to acertain if a mexican number dialled as
        10 digits is celular based on the data rates we
        got from upstream Voip.
        """
        try:
            if (len(destination_number) != 10 or
                    re.search(r'^(00|\+)', destination_number) is not None):
                return destination_number
            if self.is_number_mxcel(destination_number):
                destination_number = '0052' + destination_number
            else:
                destination_number = '0052' + destination_number
            log.info('Translated dialled 10 digit number to %s' % destination_number)
            return destination_number
        except NumberingException as _ex:
            log.error(_ex)
            return destination_number

    def is_number_did(self, destination_number):
        try:
            cur = db_conn.cursor()
            cur.execute("SELECT phonenumber FROM dids WHERE phonenumber=%(number)s", {'number': destination_number})
            did = cur.fetchone()
            db_conn.commit()
            #log.debug("Value of did var: %s" % did)
            return bool(did)
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error checking DID: %s' % e)

    def fivetoeleven(self, source_number, destination_number, logger):
        """ Convert a five digit extension to 11 digits based on the caller. """
        if len(destination_number) != 5:
            return destination_number
        elevendigit_number = source_number[:6] + destination_number
        logger.info('5 digit destination : %s->%s' % (destination_number, elevendigit_number))
        return elevendigit_number

    def is_number_local(self, destination_number):
        # check if extension if yes add internal_prefix
        if len(destination_number) == 5:
            destination_number = config['internal_prefix'] + destination_number

        try:
            cur = db_conn.cursor()
            cur.execute('SELECT msisdn FROM subscribers WHERE msisdn=%(number)s', {'number': destination_number})
            dest = cur.fetchone()
            db_conn.commit()
            if dest != None:
                destn = dest[0]
                # check if number is local to the site
                if destn[:6] == config['internal_prefix']:
                    return True
            else:
                return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error checking if number is local:' % e)

    def is_number_webphone(self, number):
        if ('webphone_prefix' in globals() and
                isinstance(webphone_prefix, list) and
                number[:5] in webphone_prefix):
            return True

    def is_number_known(self, number):
        if self.is_number_webphone(number):
            return True
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            db_conn.commit()
            subscriber = cur.fetchone()
            if subscriber != None:
                return True
            return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('PG_HLR error checking if number is known:' % e)

    def is_number_internal(self, destination_number):
        siteprefix = destination_number[:6]
        if siteprefix == config['internal_prefix']:
            return False
        # Try to avoid going to RIAK here
        cur = db_conn.cursor()
        cur.execute('SELECT DISTINCT home_bts FROM hlr WHERE msisdn like %(prefix)s', {'prefix': siteprefix+'%'})
        test = cur.fetchall()
        db_conn.commit()
        if len(test) > 1:
            log.warn('!!FIX THIS!! Got more than one home_bts from hlr for %s' % siteprefix)
            sites = riak_client.bucket('sites')
            return bool(sites.get(siteprefix).exists)
        elif len(test) == 1:
            return True
        else:
            return False

    def is_number_here(self, number):
        log.info('%s %s %s %s' % (self.calling_host, mncc_ip_address, number[:6], config['internal_prefix']))
        if self.calling_host == mncc_ip_address and number[:6] == config['internal_prefix']:
            # If we are here and are a local number, then we can't be roaming
            log.warn('%s is here' % number)
            return False

    def is_number_roaming(self, number):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT * FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            subscriber = cur.fetchone()
            db_conn.commit()
            if subscriber != None:
                if subscriber['home_bts'] != subscriber['current_bts']:
                    if subscriber['authorized'] == 1:
                        return True
                    else:
                        raise NumberingException('RK_DB subscriber %s is roaming on %s but is not authorized' %
                                                 (number, subscriber['current_bts']))
            return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('PG_HLR error checking if number is in roaming:' % e)

    def get_dhlr_entry(self, imsi):
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

    def get_local_hlr_btsinfo(self, number):
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT home_bts,current_bts FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            subscriber = cur.fetchone()
            db_conn.commit()
            if subscriber != None:
                return subscriber
            else:
                raise NumberingException('PG_DB subscriber not found: %s' % number)
            return False
        except psycopg2.DatabaseError as e:
            raise NumberingException('PG_HLR error getting bts info for:' % e)


    def get_current_bts(self, number):
        if (self.is_number_webphone(number) and
                isinstance(sip_central_ip_address, list)):
            return sip_central_ip_address[0]
        try:
            cur = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT current_bts FROM hlr WHERE msisdn=%(msisdn)s', {'msisdn': number})
            subscriber = cur.fetchone()
            db_conn.commit()
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
        return self.get_site_ip_hlr(siteprefix)

    def get_site_ip_hlr(self, siteprefix):
        cur = db_conn.cursor()
        cur.execute('SELECT DISTINCT home_bts FROM hlr WHERE msisdn like %(prefix)s', {'prefix': siteprefix+'%'})
        result = cur.fetchall()
        db_conn.commit()
        if len(result) != 1:
            log.warn('!!FIX THIS!! Did not get ONE home_bts from hlr for %s', siteprefix)
            log.debug('Trying Riak...')
            try:
                site = riak_client.bucket('sites')
                site_data = site.get(siteprefix)
                if site_data.data['ip_address'] != None:
                    return site_data.data['ip_address']
                else:
                    raise NumberingException('RK_DB Error no IP found for site %s' % site)
            except socket.error as err:
                raise NumberingException('RK_DB Connection Unavailable %s' % str(err))
        else:
            return result[0][0]

    def get_callerid(self, caller, callee):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT callerid FROM dids WHERE subscriber_number = %(caller)s LIMIT 1',
                        {'caller': caller})
            callerid = cur.fetchone()
            if not callerid is None:
                db_conn.commit()
                return callerid[0]
            if callee[0] == '+':
                dest = callee[1:2]
            if re.search(r'^00', callee) != None:
                dest = callee[2:3]
            cur.execute('SELECT callerid FROM dids,providers WHERE callerid LIKE %(prefix)s LIMIT 1',
                        {'prefix': '+'+dest+'%'})
            callerid = cur.fetchone()
            if callerid == None:
                cur.execute("SELECT callerid FROM dids,providers WHERE "
                            "providers.id = dids.provider_id AND "
                            "providers.active = 1 ORDER BY dids.id asc LIMIT 1")
                callerid = cur.fetchone()
            db_conn.commit()
            if callerid != None:
                return callerid[0]
            else:
                return None
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error getting CallerID: %s' % e)

    def get_did_subscriber(self, destination_number):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT subscriber_number FROM dids WHERE phonenumber=%(number)s',
                        {'number': destination_number})
            dest = cur.fetchone()
            db_conn.commit()
            if dest != None:
                return dest[0]
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error getting subscriber number associated to the DID: %s' % e)

    def get_gateways(self, callee):
        if not callee:
            return []
        match = callee
        if callee[0] == '+':
            match = callee[1:]
        if callee[0:2] == '00':
            match = callee[2:]
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT * FROM providers WHERE active = 1 ORDER by length(prefix) DESC')
            all_gws = cur.fetchall()
            db_conn.commit()
        except psycopg2.DatabaseError, e:
            raise NumberingException('Database error getting a Gateway: %s' % e)
        gws = []
        for gw in all_gws:
            gws.append([gw[2].strip(), gw[1].strip()])
            gws.sort(key=len, reverse=True)
        gws[:] = [x for x in gws if match.startswith(x[0])]
        return gws

    def get_gateway(self):
        try:
            cur = db_conn.cursor()
            cur.execute('SELECT provider_name FROM providers WHERE active = 1')
            gw = cur.fetchone()
            db_conn.commit()
            if gw != None:
                return gw[0]
            else:
                return None
        except psycopg2.DatabaseError as e:
            raise NumberingException('Database error getting the Gateway: %s' % e)

    def is_number_mxcel(self, destination_number):
        try:
            if len(destination_number) != 10:
                log.debug("Number %s length not 10" % destination_number)
                return False
            number = '521'+destination_number
            cur = db_conn.cursor()
            cur.execute("""SELECT d::text as d, a FROM prefix_mexico
                WHERE length(d::text) > 6 ORDER BY length(d::text) DESC
                """)
            prefixes = cur.fetchall()
            db_conn.commit()
            for prefix in prefixes:
                if number.startswith(prefix[0]):
                    log.info('MX cel Matched Prefix for "%s"', prefix[1])
                    log.debug('MX cel: %s->%s' % (destination_number, number))
                    return True
            return False
        except psycopg2.DatabaseError as e:
            db_conn.rollback()
            raise NumberingException('PG_DB error getting prefix match: %s' % e)

if __name__ == '__main__':
    num = Numbering()
    num.is_number_roaming('66666139666')
