############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# REST API Interface to RCCN Modules
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

# Python3 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import binascii
import datetime
import time
import psycopg2
import sys
import logging

from corepost.web import RESTResource, route, Http

from config import (api_log, PGEncoder, config, db_conn, use_kannel)
from modules.subscriber import (Subscriber, SubscriberException)
from modules.reseller import (Reseller, ResellerException)
from modules.credit import (Credit, CreditException)
from modules.statistics import (
    CallsStatistics,
    CostsStatistics,
    LiveStatistics,
    StatisticException,
)
from modules.configuration import (Configuration, ConfigurationException)
from modules.sms import (SMS, SMSException)


class SubscriberRESTService:
    path = '/subscriber'

    # get all subscribers
    @route('/')
    def getAll(self, request):
        api_log.info('%s - [GET] %s', request.getHost().host, self.path)
        try:
            sub = Subscriber()
            data = json.dumps(sub.get_all(), cls=PGEncoder)
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data
   
    # get subscriber
    @route('/<msisdn>')
    def get(self, request, msisdn):
        api_log.info('%s - [GET] %s/%s', request.getHost().host, self.path, msisdn)
        try:
            sub = Subscriber()
            if msisdn == 'all_connected':
                data = json.dumps(sub.get_all_connected(), cls=PGEncoder)
            elif msisdn == 'all_sip':
                data = json.dumps(sub.get_sip_connected())
            elif msisdn == 'unpaid_subscription':
                data = json.dumps(sub.get_unpaid_subscription(), cls=PGEncoder)
            elif msisdn == 'paid_subscription':
                data = json.dumps(sub.get_paid_subscription(), cls=PGEncoder)
            elif msisdn == 'unauthorized':
                data = json.dumps(sub.get_unauthorized(), cls=PGEncoder)
            elif msisdn == 'online':
                data = json.dumps(sub.get_online(), cls=PGEncoder)
            elif msisdn == 'offline':
                data = json.dumps(sub.get_offline(), cls=PGEncoder)
            elif msisdn == 'all_roaming':
                data = json.dumps(sub.get_roaming(), cls=PGEncoder)
            elif msisdn == 'all_foreign':
                if request.getClientIP().find("10.23") > -1:
                    request.setHeader('Access-Control-Allow-Origin','*')
                data = json.dumps(sub.get_all_foreign(), cls=PGEncoder)
            else:
                data = json.dumps(sub.get(msisdn), cls=PGEncoder)
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        if msisdn != 'all_connected':
            api_log.info(data)
        else:
            api_log.debug(data)

        return data

    # get msisdn
    @route('/extension/<imsi>')
    def extension(self, request, imsi):
        api_log.info('%s - [GET] %s/%s', request.getHost().host, self.path, imsi)
        try:
            sub =Subscriber()
            data = json.dumps(sub.get_local_extension(imsi), cls=PGEncoder)
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.debug(data)
        return data

 
    # add new subscriber
    @route('/', Http.POST)
    def post(self, request, msisdn, name, balance, location, equipment):
        api_log.info(
            '%s - [POST] %s Data: msisdn:"%s" name:"%s" balance:"%s" location:"%s equipment:"%s"',
            request.getHost().host, self.path, msisdn, name, balance, location, equipment
        )
        try:
            sub = Subscriber()
            num = sub.add(msisdn, name, balance, location, equipment)
            if num != msisdn:
                data = {'status': 'success', 'error': num}
            else:
                data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    # put subscriber offline
    @route('/offline', Http.PUT)
    def offline(self, request, msisdn='', local='no'):
        api_log.info('%s - [PUT] %s/offline Data: msisdn: "%s"', request.getClientIP(), self.path, msisdn)
        try:
            sub = Subscriber()
            sub.expire_lu(msisdn)
            data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}
            api_log.debug(data)
            return data
        # Take advantage to point this subscriber to the new location in our hlr
        # so we (at least) don't have to wait for the next hlr sync run
        try:
            if local == 'yes':
                current_bts = config['local_ip']
            else:
                current_bts = request.getClientIP()
            cur = db_conn.cursor()
            now = datetime.datetime.fromtimestamp(int(time.time()))
            cur.execute('UPDATE hlr SET current_bts=%(current_bts)s, updated=%(updated)s WHERE msisdn=%(msisdn)s',
            {'msisdn': msisdn, 'current_bts': current_bts, 'updated': now})
            db_conn.commit()
        except psycopg2.DatabaseError as e:
            data = {'status': 'failed', 'error': str(e)}
            api_log.debug(data)
            return data
        api_log.debug(data)
        return data

    # edit subscriber
    @route('/<msisdn>', Http.PUT)
    def put(self, request, msisdn='', name='', balance='', authorized='', 
        subscription_status='', location='', equipment='', roaming=''):
        api_log.info(
            '%s - [PUT] %s/%s Data: name:"%s" balance:"%s" authorized:"%s" ' 
            'subscription_status:"%s" location:"%s" equipment:"%s" roaming:"%s"',
            request.getHost().host,
            self.path,
            msisdn,
            name,
            balance,
            authorized,
            subscription_status,
            location,
            equipment,
            roaming
        )
        try:
            sub = Subscriber()
            if subscription_status != '':
                sub.subscription(msisdn, subscription_status)
            if  authorized != '':
                sub.authorized(msisdn, authorized)
            if msisdn != '' and name != '' or balance != '':
                sub.edit(msisdn, name, balance, location, equipment, roaming)
            data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    # delete subscriber
    @route('/<msisdn>', Http.DELETE)
    def delete(self, request, msisdn):
        api_log.info('%s - [DELETE] %s/%s', request.getHost().host, self.path, msisdn)
        try:
            sub = Subscriber()
            sub.delete(msisdn)
            data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # Get List of IMEI for autocomplete
    @route('/imei')
    def imei(self, request):
        api_log.info('%s - [GET] %s', request.getHost().host, self.path)
        try:
            sub = Subscriber()
            data = json.dumps(sub.get_imei_autocomplete())
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.debug(data)
        return data

    @route('/imei/<partial_imei>')
    def imei(self, request, partial_imei):
        api_log.info('%s - [GET] %s/%s', request.getHost().host, self.path, partial_imei)
        try:
            sub = Subscriber()
            data = json.dumps(sub.get_imei_autocomplete(partial_imei))
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.debug(data)
        return data

class ResellerRESTService:
    path = '/reseller'
   
    # get all resellers
    @route('/')
    def getAll(self, request):
        api_log.info('%s - [GET] %s', request.getHost(). host, self.path)
        try:
            reseller = Subscriber()
            data = json.dumps(reseller.get_all(), cls=PGEncoder)
        except ResellerException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # get reseller
    @route('/<msisdn>')
    def get(self, request, msisdn):
        api_log.info('%s - [GET] %s/%s', request.getHost().host, self.path , msisdn)
        try:
            reseller = Reseller()
            if msisdn == 'messages':
                data = json.dumps(reseller.get_messages(), cls=PGEncoder)
            else:
                data = json.dumps(reseller.get(msisdn), cls=PGEncoder)
        except ResellerException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # add new reseller
    @route('/<msisdn>', Http.POST)
    def post(self, request, msisdn, pin, balance):
        api_log.info(
            '%s - [POST] %s Data: msisdn:"%s" pin:"%s" balance:"%s"',
            request.getHost().host, self.path, msisdn, pin, balance
        )
        try:
            reseller = Reseller()
            reseller.add(msisdn, pin, balance)
            data = {'status': 'success', 'error': ''}
        except ResellerException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # edit reseller
    @route('/', Http.PUT)
    def put(self, request, msisdn='', pin='', balance=''):
        api_log.info(
            '%s - [PUT] %s Data: msisdn:"%s" pin:"%s" balance:"%s"',
            request.getHost().host, self.path, msisdn, pin, balance
        )
        try:
            reseller = Reseller()
            if msisdn != '' and pin != '' or balance != '':
                reseller.edit(msisdn, pin, balance)
            data = {'status': 'success', 'error': ''}
        except ResellerException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # edit reseller notification messages
    @route('/edit_messages', Http.PUT)
    def put(self, request, mess1, mess2, mess3, mess4, mess5, mess6):
        api_log.info(
            '%s - [PUT] %s/edit_messages Data: mess1:"%s" mess2:"%s" mess3:"%s" mess4:"%s" mess5:"%s" mess6:"%s"',
            request.getHost().host, self.path, mess1, mess2, mess3, mess4, mess5, mess6
        )
        try:
            reseller = Reseller()
            reseller.edit_messages(mess1, mess2, mess3, mess4, mess5, mess6)
            data = {'status': 'success', 'error': ''}
        except ResellerException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data

    # delete reseller
    @route('/<msisdn>', Http.DELETE)
    def delete(self, request, msisdn):
        api_log.info('%s - [DELETE] %s/%s', request.getHost().host, self.path, msisdn)
        try:
            reseller = Reseller()
            reseller.delete(msisdn)
            data = {'status': 'success', 'error': ''}
        except ResellerException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

class CreditRESTService:
    path = '/credit'
    @route('/', Http.GET)
    def get(self, request):
        api_log.info('%s - [GET] %s/', request.getHost().host, self.path)
        try:
            credit = Credit()
            data = json.dumps(credit.get_all_credit_allocated(), cls=PGEncoder)
        except CreditException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.debug(data)
        return data

    @route('/records', Http.GET)
    def records(self, request, year):
        api_log.info('%s - [GET] %s/records %s', request.getHost().host, self.path, year)
        try:
            credit = Credit()
            data = json.dumps(credit.get_credit_records(year), cls=PGEncoder)
        except CreditException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.debug(data)
        return data

    @route('/month', Http.POST)
    def month(self, request, year, month):
        api_log.info('%s - [POST] %s/month %s %s', request.getHost().host, self.path, year, month)
        try:
            credit = Credit()
            data = json.dumps(credit.get_month_credit(year, month), cls=PGEncoder)
        except CreditException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.debug(data)
        return data

    @route('/', Http.POST)
    def post(self, request, msisdn, amount):
        api_log.info(
            '%s - [POST] %s/add Data: msisdn:"%s" amount:"%s"',
            request.getHost().host, self.path, msisdn, amount
        )
        try:
            credit = Credit()
            credit.add(msisdn, amount)
            data = {'status': 'success', 'error': ''}
        except CreditException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data

    @route('/reseller', Http.POST)
    def reseller(self, request, msisdn, amount):
        api_log.info(
            '%s - [POST] %s/reseller Data: msisdn:"%s" amount:"%s"',
            request.getHost().host, self.path, msisdn, amount
        )
        try:
            credit = Credit()
            credit.add_to_reseller(msisdn, amount)
            data = {'status': 'success', 'error': ''}
        except CreditException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data

class ChatRESTService:
    path = '/chat'

    @route('/', Http.POST)
    def receive(self, request, source, destination, charset, coding, text):
        try:
            sms = SMS()
            import threading
            thread = threading.Thread(target=sms.receive, args=(source, destination, text, charset, coding))
            thread.daemon = True
            api_log.info('Starting thread for chat message to %s via %s', destination, request.getClientIP())
            thread.start()
            data = {'status': 'success', 'error': ''}
            api_log.debug(data)
            return data
        except Exception as e:
            api_log.error("Chat handler exception %s", e, exc_info=True)

class SMSRESTService:
    path = '/sms'

    @route('/', Http.POST)
    def receive(self, request, source, destination, charset, coding, text, btext='', dr='', dcs=''):
        
        if btext == '':
            btext = text
        thex = binascii.hexlify(btext)

        api_log.info(
            '%s - [POST] %s Data: source:"%s" destination:"%s" charset:"%s"',
            request.getHost().host, self.path, source, destination, charset
        )
        api_log.debug(
            'Data: source:"%s" destination:"%s" charset:"%s" coding: "%s" content: %s HexofBin: %s DR: %s DCS: %s',
            source, destination, charset, coding, text.decode(charset,'replace'), thex, dr, dcs
        )
        sms = SMS()
        unicode_text = text.decode(charset,'replace')
        if use_kannel == 'yes':
            # Kannel posts to:
            # post-url = "http://localhost:8085/sms?source=%p&destination=%P&charset=%C&coding=%c&text=%a&btext=%b&dr=%d&dcs=%O"
            # Kannel sends us GSM0338 but sets charset param to UTF-8
            if coding == '0':
                try:
                    unicode_text = sms.check_decode0338(btext)
                    api_log.info('SMS Decoded from GSM 03.38')
                    api_log.debug('Decoded text:"%s"', unicode_text)
                except Exception as ex:
                    api_log.debug('Coding(%s), but: %s', coding, str(ex), exc_info=True)
                    data = {'status': 'failed', 'error': str(ex)+' '+str(sys.exc_info()[1])}
                    # It's probably utf-8
                    unicode_text=btext.decode('utf-8','replace')
            elif coding == '2' and charset == 'UTF-16BE':
                try:
                    unicode_text=btext.decode('utf-16be')
                    api_log.info('SMS decoded as UTF-16BE')
                    api_log.debug('Decoded text: "%s"', text)
                except Exception as e: # Catch Everything, try to not actually LOSE messages!
                    api_log.debug('Exception: %s', e, exc_info=True)
                    # Some phones are sending multi part messages with different charsets.
                    # Kannel concatenates and sends as UTF-16BE coding 2
                    try:
                        api_log.info('Trying multi part trick')
                        a=btext[:134]
                        b=btext[134:]
                        unicode_text=a.decode('utf-16be')+b.decode('utf8')
                    except Exception as e:
                        api_log.debug('Exception: %s', e, exc_info=True)
                        unicode_text=btext.decode('utf-16be','replace')
            else:
                unicode_text=btext.decode('utf-8','replace')
        try:
            sms.receive(source, destination, unicode_text, charset, coding)
            data = {'status': 'success', 'error': ''}
        except SMSException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/send', Http.POST)
    def send(self, request, source, destination, text):
        api_log.info(
            '%s - [POST] %s/send Data: source:"%s" destination:"%s text: %s"',
            request.getHost().host, self.path, source, destination, text
        )
        try:
            sms = SMS()
            sms.send(source, destination, text)
            data = {'status': 'success', 'error': ''}
        except Exception as e:
            api_log.info('SMS Exception: %s', e, exc_info=True)
            data = {'status': 'failed', 'error': str(e)+' '+str(sys.exc_info()[1])}
        
        api_log.info(data)
        return data

    @route('/send_broadcast', Http.POST)    
    def send_broadcast(self, request, text, btype, location):
        api_log.info(
            '%s - [POST] %s/send_broadcast Data: text:"%s" btype:[%s] location:"%s"',
             request.getHost().host, self.path, text, btype, location
        )
        try:
            sms = SMS()
            sms.send_broadcast(text, btype, location)
            data = {'status': 'success', 'error': ''}
        except SMSException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

class StatisticsRESTService:
    path = '/statistics'

    @route('/feed')
    def monitor_feed(self,request):
        api_log.info('%s - [GET] %s/feed', request.getHost().host, self.path)
        if request.getClientIP().find("10.23") > -1:
            request.setHeader('Access-Control-Allow-Origin','*')
        else:
            return ''
        try:
            stats = LiveStatistics()
            data = json.dumps(stats.monitor_feed(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.debug(data)
        return data

    @route('/sms/stat')
    def get_sms_stat(self, request, year, month):
        api_log.info('%s - [GET] %s/calls/obm', request.getHost().host, self.path)
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_sms_stat(year, month), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.debug(data)
        return str(data)

    @route('/calls/obm')
    def get_outbound_mins(self, request, year, month):
        api_log.info('%s - [GET] %s/calls/obm', request.getHost().host, self.path)
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_outbound_minutes(year, month), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.debug(data)
        return str(data)

    # Calls statistics
    @route('/calls/total_calls')
    def total_calls(self, request):
        api_log.info('%s - [GET] %s/calls/total_calls', request.getHost().host, self.path)
        try:
            stats = CallsStatistics()
            data = stats.get_total_calls()
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return str(data)

    @route('/calls/total_minutes')
    def total_minutes(self, request):
        api_log.info('%s - [GET] %s/calls/total_minutes', request.getHost().host, self.path)
        try:
            stats = CallsStatistics()
            data = stats.get_total_minutes()
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return str(data)

    @route('/calls/average_call_duration')
    def average_call_duration(self, request):
        api_log.info('%s - [GET] %s/calls/average_call_duration', request.getHost().host, self.path)
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_average_call_duration(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/calls/total_calls_by_context',Http.POST)
    def total_calls_by_context(self, request, context):
        api_log.info(
            '%s - [POST] %s/calls/total_calls_by_context Data: context:"%s"',
            request.getHost().host, self.path, context
        )
        try:
            stats = CallsStatistics()
            data = stats.get_total_calls_by_context(context)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/calls/calls',Http.POST)
    def calls(self, request, period):
        api_log.info('%s - [POST] %s/calls/calls Data: period:"%s"', request.getHost().host, self.path, period)
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_calls_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data
    
    @route('/calls/calls_minutes',Http.POST)
    def calls_minutes(self, request, period):
        api_log.info('%s - [POST] %s/calls/calls_minutes Data: period:"%s"', request.getHost().host, self.path, period)
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_calls_minutes_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data
    
    @route('/calls/calls_context',Http.POST)
    def calls_context(self, request, period):
        api_log.info('%s - [POST] %s/calls/calls_context Data: period:"%s"', request.getHost().host, self.path, period)
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_calls_context_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    # Costs/Credits statistics
    @route('/costs/total_spent')
    def total_spent(self, request):
        api_log.info('%s - [GET] %s/costs/total_spent', request.getHost().host, self.path)
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_total_spent(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data
    
    @route('/costs/average_call_cost')
    def average_call_cost(self, request):
        api_log.info('%s - [GET] %s/costs/average_call_cost', request.getHost().host, self.path)
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_average_call_cost(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/total_spent_credits')
    def total_spent_credits(self, request):
        api_log.info('%s - [GET] %s/costs/total_spent_credits', request.getHost().host, self.path)
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_total_spent_credits(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/top_destinations')
    def top_destinations(self, request):
        api_log.info('%s - [GET] %s/top_destinations', request.getHost().host, self.path)
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_top_destinations(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/costs_stats', Http.POST)
    def costs_stats(self, request, period):
        api_log.info('%s - [POST] %s/costs/costs_stats Data: period:"%s"', request.getHost().host, self.path, period)
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_costs_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/credits_stats',Http.POST)
    def credits_stats(self, request, period):
        api_log.info('%s - [POST] %s/costs/credits_stats Data: period:"%s"', request.getHost().host, self.path, period)
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_credits_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

class ConfigurationRESTService:
    path = '/configuration'

    @route('/site', Http.GET)
    def site(self, request):
        api_log.debug('%s - [GET] %s/site', request.getHost().host, self.path)
        try:
            config = Configuration()
            data = json.dumps(config.get_site(), cls=PGEncoder)
        except ConfigurationException as e:
            data = {'status': 'failed', 'error': str(e)}
    
        api_log.debug(data)
        return data

    @route('/locations', Http.GET)
    def locations(self, request):
        api_log.debug('%s - [GET] %s/locations', request.getHost().host, self.path)
        try:
            config = Configuration()
            data = json.dumps(config.get_locations(), cls=PGEncoder)
        except ConfigurationException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.debug(data)
        return data
    
    @route('/config', Http.GET)
    def config(self, request):
        api_log.debug('%s - [GET] %s/config', request.getHost().host, self.path)
        try:
            config = Configuration()
            data = json.dumps(config.get_site_config(), cls=PGEncoder)
        except ConfigurationException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.debug(data)
        return data


def run_rapi():
    api_log.info('Starting up RCCN API manager')
    app = RESTResource((SubscriberRESTService(), ResellerRESTService(), CreditRESTService(), StatisticsRESTService(), SMSRESTService(), ChatRESTService(), ConfigurationRESTService()))
    app.run(8085)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1]=='debug':
            api_log.setLevel(logging.DEBUG)
    run_rapi()
