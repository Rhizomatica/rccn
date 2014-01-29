############################################################################
# 
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# SMS module
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

import urllib
from subscriber import Subscriber, SubscriberException 
from numbering import Numbering, NumberingException

class SMSException(Exception):
        pass

class SMS:

	def __init__(self):
		self.server = 'localhost'
		self.port = 14002
		self.username = 'kannel'
		self.password = 'kannel'
		self.charset = 'utf-8'
		self.coding = 0

	def receive(self, source, destination, text):
		log.info('Received SMS: %s %s %s' % (source, destination, text))
		# SMS_LOCAL | SMS_INTERNAL | SMS_INBOUND | SMS_OUTBOUND | SMS_ROAMING

		# check if destination number is local
		try:
			numbering = Numbering()
                        num_res = numbering.is_number_local(destination)

			if num_res == 0:
				log.info('SMS_LOCAL check if subscriber is authorized')
				# check if subscriber is authorized
				try:
					sub = Subscriber()
					if sub.is_authorized(source) and sub.is_authorized(destination):
						log.info('Forward SMS back to BSC')
						# number is local send SMs back to SMSc
						self.send(source,destination,text)
					else:
						
						return
				except SubscriberException as e:
					log.error(e)
			elif num_res == 1:
				# number is internal send SMS to correct site
				return
			else:
		
				# dest number is not local, check if dest number is a shortcode
				if destination in extensions_list:
					log.info('Destination number is a shortcode, execute shortcode handler')
					shortcode = importlib.import_module('extensions.ext_'+self.destination, 'extensions')
					try:
						log.debug('Exec shortcode handler')
						extension.handler('',source, destination, text)
					except ExtensionException as e:
						log.error(e)
				else:
				# dest number is for an external number send sms to sms provider
					return
		except NumberingException as e:
			log.error(e)
	
	def send(self, source, destination, text, server='localhost'):
		log.info('Send SMS: %s %s %s' % (source, destination, text))
		enc_text = urllib.quote(text)
		try:
                        res = urllib.urlopen(
                                "http://%s:%d/cgi-bin/sendsms?username=%s&password=%s&charset=%s&coding=%d&to=%s&from=%s&text=%s"\
                                % (server, self.port, self.username, self.password, self.charset, self.coding, destination, source, enc_text)
                        ).read()
                except IOError:
                        raise SMSException('Error connecting to Kannel to send SMS: %s' % e)



	

if __name__ == '__main__':
	sms = SMS()
	#sub.set_balance('68820110010',3.86)
	try:
		#sub.add('37511','Antanz',4.00)
		#sub.edit('68820137511','Antanz_edit',3.86)
		sms.send('666','68820138310','prot')
		#credit.add('INV00','68820137514', 1.00)
		#a = sub.get('68820137511')
		#print a
		#sub.delete('68820137511')
	except SMSException as e:
		print "Error: %s" % e

