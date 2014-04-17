import sys
sys.path.append("..")
from config import *

def handler(session, *args):
	log.debug('Handler for ext 888')
	calling_number = session.getVariable('caller_id_number')
	sms = SMS()
	try:
		sub = Subscriber()
		current_subscriber_balance = sub.get_balance(calling_number)
	except SubscriberException as e:
		log.error('Calling number %s unauthorized' % calling_number)
		sms.send(config['smsc'],calling_number,config['sms_source_unauthorized'])
		raise ExtensionException(e)

	session.answer()
	session.execute('playback', '006_mensaje_saldo_actual.gsm')
	text = 'Su saldo actual es de %s pesos' % current_subscriber_balance
	log.info('Send SMS to %s: %s' % (calling_number, text))
	sms.send(config['smsc'],calling_number,text)
	session.hangup()

