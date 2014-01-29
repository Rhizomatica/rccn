import sys
sys.path.append("..")
from config import *

import obscvty

def handler(session):
	log.debug('Handler for ext 888')
	calling_number = session.getVariable('caller_id_number')
	try:
		sub = Subscriber()
		current_subscriber_balance = sub.get_balance(calling_number)
	except SubscriberException as e:
		raise ExtensionException(e)

	session.answer()
	session.execute('playback', '006_mensaje_saldo_actual.gsm')
	text = 'Su saldo actual es de %s pesos' % current_subscriber_balance
	log.info('Send SMS to %s: %s' % (calling_number, text))
	send_sms(calling_number,text)
	session.hangup()


def send_sms(num, text):
	appstring = "OpenBSC"
	appport = 4242
	vty = obscvty.VTYInteract(appstring, "127.0.0.1", appport)
	cmd = 'subscriber extension %s sms sender extension 10000 send %s' % (num,text)
	vty.command(cmd)


if __name__ == '__main__':
	send_sms('68820141325', 'test')
