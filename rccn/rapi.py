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

from corepost import Response, NotFoundException, AlreadyExistsException
from corepost.web import RESTResource, route, Http 
from config import *

class SubscriberRESTService:
    path = '/subscriber'

    # get all subscribers
    @route('/')
    def getAll(self, request):
        api_log.info('%s - [GET] %s' % (request.getHost().host, self.path))
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
        api_log.info('%s - [GET] %s/%s' % (request.getHost().host, self.path, msisdn))
        try:
            sub = Subscriber()
            if msisdn == 'all_connected':
                data = json.dumps(sub.get_all_connected(), cls=PGEncoder)
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
            else:
                data = json.dumps(sub.get(msisdn), cls=PGEncoder)
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        if msisdn != 'all_connected':
            api_log.info(data)

        return data

    # get msisdn
    @route('/extension/<imsi>')
    def extension(self, request, imsi):
	api_log.info('%s - [GET] %s/%s' % (request.getHost().host, self.path, imsi))
	try:
		sub =Subscriber()
		data = json.dumps(sub.get_local_extension(imsi), cls=PGEncoder)
	except SubscriberException as e:
		data = {'status': 'failed', 'error': str(e)}
	return data

 
    # add new subscriber
    @route('/', Http.POST)
    def post(self, request, msisdn, name, balance, location):
        api_log.info('%s - [POST] %s Data: msisdn:"%s" name:"%s" balance:"%s" location:"%s"' % (request.getHost().host, self.path, msisdn, name, balance, location))
        try:
            sub = Subscriber()
            num = sub.add(msisdn, name, balance, location)
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
    def offline(self, request, imsi=''):
        api_log.info('%s - [PUT] %s/offline Data: imsi:"%s"' % (request.getHost().host, self.path, imsi))
        try:
            sub = Subscriber()
            sub.set_lac(imsi, 0)
            data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # edit subscriber
    @route('/<msisdn>', Http.PUT)
    def put(self, request, msisdn='', name='', balance='', authorized='', subscription_status='', location=''):
        api_log.info('%s - [PUT] %s/%s Data: name:"%s" balance:"%s" authorized:"%s" subscription_status:"%s" location:"%s"' % (request.getHost().host, self.path, 
        msisdn, name, balance, authorized, subscription_status, location))
        try:
            sub = Subscriber()
            if  authorized != '':
                sub.authorized(msisdn, authorized)
            if subscription_status != '':
                sub.subscription(msisdn, subscription_status)
            if msisdn != '' and name != '' or balance != '':
                sub.edit(msisdn, name, balance, location)
            data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data

    # delete subscriber
    @route('/<msisdn>', Http.DELETE)
    def delete(self, request, msisdn):
        api_log.info('%s - [DELETE] %s/%s' % (request.getHost().host, self.path, msisdn))
        try:
            sub = Subscriber()
            sub.delete(msisdn)
            data = {'status': 'success', 'error': ''}
        except SubscriberException as e:
            data = {'status': 'failed', 'error': str(e)}

        api_log.info(data)
        return data
        
class ResellerRESTService:
    path = '/reseller'
   
    # get all resellers
    @route('/')
    def getAll(self, request):
        api_log.info('%s - [GET] %s' % (request.getHost(). host, self.path))
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
        api_log.info('%s - [GET] %s/%s' % (request.getHost().host, self.path , msisdn))
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
        api_log.info('%s - [POST] %s Data: msisdn:"%s" pin:"%s" balance:"%s"' % (request.getHost().host, self.path, msisdn, pin, balance))
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
        api_log.info('%s - [PUT] %s Data: msisdn:"%s" pin:"%s" balance:"%s"' % (request.getHost().host, self.path, msisdn, pin, balance))
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
        api_log.info('%s - [PUT] %s/edit_messages Data: mess1:"%s" mess2:"%s" mess3:"%s" mess4:"%s" mess5:"%s" mess6:"%s"' % (request.getHost().host, self.path, 
        mess1, mess2, mess3, mess4, mess5, mess6))
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
        api_log.info('%s - [DELETE] %s/%s' % (request.getHost().host, self.path, msisdn))
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

    @route('/', Http.POST)
    def post(self, request, msisdn, amount):
        api_log.info('%s - [POST] %s/add Data: msisdn:"%s" amount:"%s"' % (request.getHost().host, self.path, msisdn, amount))
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
        api_log.info('%s - [POST] %s/reseller Data: msisdn:"%s" amount:"%s"' % (request.getHost().host, self.path, msisdn, amount))
        try:
            credit = Credit()
            credit.add_to_reseller(msisdn, amount)
            data = {'status': 'success', 'error': ''}
        except CreditException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data

class SMSRESTService:
    path = '/sms'

    @route('/', Http.POST)
    def receive(self, request, source, destination, charset, coding, text):
        api_log.info('%s - [POST] %s Data: source:"%s" destination:"%s"  charset:"%s" coding: "%s" text:"%s"' % (request.getHost().host, self.path, source,
        destination, charset, coding, text))
        try:
            sms = SMS()
            sms.receive(source, destination, text, charset, coding)
            data = {'status': 'success', 'error': ''}
        except SMSException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data

    @route('/send', Http.POST)
    def send(self, request, source, destination, text):
        api_log.info('%s - [POST] %s/send Data: source:"%s" destination:"%s" text:"%s"' % (request.getHost().host, self.path, source, destination, text))
        try:
            sms = SMS()
            sms.send(source, destination, text)
            data = {'status': 'success', 'error': ''}
        except SMSException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data

    @route('/send_broadcast', Http.POST)    
    def send_broadcast(self, request, text, btype):
        api_log.info('%s - [POST] %s/send_broadcast Data: text:"%s" btype:"%s"' % (request.getHost().host, self.path, text, btype))
        try:
            sms = SMS()
            sms.send_broadcast(text, btype)
            data = {'status': 'success', 'error': ''}
        except SMSException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

class StatisticsRESTService:
    path = '/statistics'

    # Calls statistics
    @route('/calls/total_calls')
    def total_calls(self, request):
        api_log.info('%s - [GET] %s/calls/total_calls' % (request.getHost().host, self.path))
        try:
            stats = CallsStatistics()
            data = stats.get_total_calls()
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/calls/total_minutes')
    def total_minutes(self, request):
        api_log.info('%s - [GET] %s/calls/total_minutes' % (request.getHost().host, self.path))
        try:
            stats = CallsStatistics()
            data = stats.get_total_minutes()
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/calls/average_call_duration')
    def average_call_duration(self, request):
        api_log.info('%s - [GET] %s/calls/average_call_duration' % (request.getHost().host, self.path))
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_average_call_duration(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/calls/total_calls_by_context',Http.POST)
    def total_calls_by_context(self, request, context):
        api_log.info('%s - [POST] %s/calls/total_calls_by_context Data: context:"%s"' % (request.getHost().host, self.path, context))
        try:
            stats = CallsStatistics()
            data = stats.get_total_calls_by_context(context)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/calls/calls',Http.POST)
    def calls(self, request, period):
        api_log.info('%s - [POST] %s/calls/calls Data: period:"%s"' % (request.getHost().host, self.path, period))
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_calls_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data
    
    @route('/calls/calls_minutes',Http.POST)
    def calls_minutes(self, request, period):
        api_log.info('%s - [POST] %s/calls/calls_minutes Data: period:"%s"' % (request.getHost().host, self.path, period))
        try:
            stats = CallsStatistics()
            data = json.dumps(stats.get_calls_minutes_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data
    
    @route('/calls/calls_context',Http.POST)
    def calls_context(self, request, period):
        api_log.info('%s - [POST] %s/calls/calls_context Data: period:"%s"' % (request.getHost().host, self.path, period))
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
        api_log.info('%s - [GET] %s/costs/total_spent' % (request.getHost().host, self.path))
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_total_spent(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data
    
    @route('/costs/average_call_cost')
    def average_call_cost(self, request):
        api_log.info('%s - [GET] %s/costs/average_call_cost' % (request.getHost().host, self.path))
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_average_call_cost(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/total_spent_credits')
    def total_spent_credits(self, request):
        api_log.info('%s - [GET] %s/costs/total_spent_credits' % (request.getHost().host, self.path))
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_total_spent_credits(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/top_destinations')
    def top_destinations(self, request):
        api_log.info('%s - [GET] %s/top_destinations' % (request.getHost().host, self.path))
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_top_destinations(), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/costs_stats', Http.POST)
    def costs_stats(self, request, period):
        api_log.info('%s - [POST] %s/costs/costs_stats Data: period:"%s"' % (request.getHost().host, self.path, period))
        try:
            stats = CostsStatistics()
            data = json.dumps(stats.get_costs_stats(period), cls=PGEncoder)
        except StatisticException as e:
            data = {'status': 'failed', 'error': str(e)}
        api_log.info(data)
        return data

    @route('/costs/credits_stats',Http.POST)
    def credits_stats(self, request, period):
        api_log.info('%s - [POST] %s/costs/credits_stats Data: period:"%s"' % (request.getHost().host, self.path, period))
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
        api_log.info('%s - [GET] %s/site' % (request.getHost().host, self.path))
        try:
            config = Configuration()
            data = json.dumps(config.get_site(), cls=PGEncoder)
        except ConfigurationException as e:
            data = {'status': 'failed', 'error': str(e)}
    
        api_log.info(data)
        return data

    @route('/locations', Http.GET)
    def locations(self, request):
        api_log.info('%s - [GET] %s/locations' % (request.getHost().host, self.path))
        try:
            config = Configuration()
            data = json.dumps(config.get_locations(), cls=PGEncoder)
        except ConfigurationException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data
    
    @route('/config', Http.GET)
    def config(self, request):
        api_log.info('%s - [GET] %s/config' % (request.getHost().host, self.path))
        try:
            config = Configuration()
            data = json.dumps(config.get_site_config(), cls=PGEncoder)
        except ConfigurationException as e:
            data = {'status': 'failed', 'error': str(e)}
        
        api_log.info(data)
        return data


def run_rapi():
    api_log.info('Starting up RCCN API manager')
    app = RESTResource((SubscriberRESTService(), ResellerRESTService(), CreditRESTService(), StatisticsRESTService(), SMSRESTService(), ConfigurationRESTService()))
    app.run(8085)

if __name__ == "__main__":
    run_rapi()
