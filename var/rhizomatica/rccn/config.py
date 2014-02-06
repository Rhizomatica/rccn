import sys, os, logging, time, re, glob, importlib
import psycopg2
import psycopg2.extras
import sqlite3
import json
import riak
from logging import handlers as loghandlers
from decimal import Decimal
from datetime import date

class PGEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, date):
			return str(obj)
		if isinstance(obj, Decimal):
			return str(obj)
		return json.JSONEncoder.default(self, obj)


# paths
rhizomatica_dir = '/var/rhizomatica'
sq_hlr_path = '/var/lib/osmocom/hlr.sqlite3'

# Loggers
smlog = loghandlers.RotatingFileHandler(rhizomatica_dir+'/rccn/log/rccn.log', 'a', 104857600, 5)
formatter = logging.Formatter('%(asctime)s => %(name)-7s: %(levelname)-8s %(message)s')
smlog.setFormatter(formatter)

blog = loghandlers.RotatingFileHandler(rhizomatica_dir+'/rccn/log/billing.log', 'a', 104857600, 5)
blog.setFormatter(formatter)
logging.basicConfig()

alog = loghandlers.RotatingFileHandler(rhizomatica_dir+'/rccn/log/api.log', 'a', 104857600, 5)
formatter_api = logging.Formatter('%(asctime)s => %(name)-7s: %(levelname)-8s %(message)s')
alog.setFormatter(formatter)
logging.basicConfig()

slog = loghandlers.RotatingFileHandler(rhizomatica_dir+'/rccn/log/subscription.log', 'a', 104857600, 5)
formatter_slog = logging.Formatter('%(asctime)s => %(name)-7s: %(levelname)-8s %(message)s')
slog.setFormatter(formatter)
logging.basicConfig()

# initialize logger RCCN
log = logging.getLogger('RCCN')
log.addHandler(smlog)
log.setLevel( logging.DEBUG)

# initialize logger Biller
bill_log= logging.getLogger('RCCN_BILLING')
bill_log.addHandler(blog)
bill_log.setLevel(logging.DEBUG)

# initialize logger API
api_log = logging.getLogger('RCCN_API')
api_log.addHandler(alog)
api_log.setLevel(logging.DEBUG)

# initialize logger RSC
subscription_log = logging.getLogger('RCCN_RSC')
subscription_log.addHandler(slog)
subscription_log.setLevel(logging.DEBUG)


# Extensions
class ExtensionException(Exception):
        pass

extensions_list = []
os.chdir(rhizomatica_dir+'/rccn/extensions/')
files = glob.glob(rhizomatica_dir+'/rccn/extensions/ext_*.py')
for f in files:
        file_name = f.rpartition('.')[0]
        ext_name = file_name.split('_')[1]
        extensions_list.append(ext_name)


# initialize DB handler
db_conn = None
config = {}
try:
	db_conn = psycopg2.connect(database='rhizomatica', user='rhizomatica', password='xEP3Y4W8gG*4*zu',host='localhost')
	cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	cur.execute('SELECT * from site')
	site_conf = cur.fetchone()
	
	config['site_name'] = site_conf['site_name']
	config['internal_prefix'] = site_conf['postcode']+site_conf['pbxcode']
	config['local_ip'] = site_conf['ip_address']
	
except psycopg2.DatabaseError, e:
	log.error('Database connection error %s' % e)


# load modules
from modules import subscriber
Subscriber = subscriber.Subscriber
SubscriberException = subscriber.SubscriberException

from modules import numbering
Numbering = numbering.Numbering
NumberingException = numbering.NumberingException

from modules import billing
Billing = billing.Billing

from modules import credit
Credit = credit.Credit
CreditException = credit.CreditException

from modules import configuration
Configuration = configuration.Configuration
ConfigurationException = configuration.ConfigurationException

from modules import statistics
CallsStatistics = statistics.CallsStatistics
CostsStatistics = statistics.CostsStatistics
StatisticException = statistics.StatisticException

from modules import sms
SMS = sms.SMS
SMSException = sms.SMSException

from modules import subscription
Subscription = subscription.Subscription
SubscriptionException = subscription.SubscriptionException
