import sys
sys.path.append("..")
from config import *

def handler(session, *args):
	log.debug('Handler for ext 778')
	calling_number = session.getVariable('caller_id_number')
	sms = SMS()
	try:
		reseller = Reseller()
		reseller.reseller_msisdn = calling_number
		current_reseller_balance = reseller.get_balance()
	except ResellerException as e:
		raise ExtensionException(e)

	session.answer()
	session.execute('playback', '006_mensaje_saldo_actual.gsm')
	text = 'Su revendidores saldo actual es de %s pesos' % current_subscriber_balance
	log.info('Send SMS to %s: %s' % (calling_number, text))
	sms.send(config['smsc'],calling_number,text)
	session.hangup()

