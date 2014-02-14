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

import urllib, obscvty
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
		self.context = ''

	def receive(self, source, destination, text, charset, coding):
		self.charset = charset
		self.coding = coding

		sms_log.info('Received SMS: %s %s %s' % (source, destination, text))
		# SMS_LOCAL | SMS_INTERNAL | SMS_INBOUND | SMS_OUTBOUND | SMS_ROAMING

		try:
			numbering = Numbering()
			if numbering.is_number_local(destination) == True:
				sms_log.info('SMS_LOCAL check if subscriber is authorized')
				# check if subscriber is authorized
				try:
					sub = Subscriber()
					if sub.is_authorized(source,0) and sub.is_authorized(destination,0):
						sms_log.info('Forward SMS back to BSC')
						# number is local send SMS back to SMSc
						self.context = 'SMS_LOCAL'
						self.send(source,destination,text)
					else:
						if numbering.is_number_internal(source) == True:
							sms_log.info('SMS_INTERNAL Forward SMS back to BSC')
							self.context = 'SMS_INTERNAL'
							self.send(source,destination,text)
						else:
							if sub.is_authorized(destination,0):
        	                                                sms_log.info('SMS_INBOUND Forward SMS back to BSC')
                	                                        # number is local send SMS back to SMSc
								self.context = 'SMS_INBOUND'
                                	                        self.send(source,destination,text)
                                        	        else:
								sms_log.error('Shouldn\'t be get here')
	                                                        return

				except SubscriberException as e:
					raise SMSException('Receive SMS error: %s' % e)
			else:
		
				# dest number is not local, check if dest number is a shortcode
				if destination in extensions_list:
					sms_log.info('Destination number is a shortcode, execute shortcode handler')
					shortcode = importlib.import_module('extensions.ext_'+destination, 'extensions')
					try:
						sms_log.debug('Exec shortcode handler')
						extension.handler('',source, destination, text)
					except ExtensionException as e:
						raise SMSException('Reiceve SMS error: %s' % e)
				else:
					# check if sms is for another location
					if numbering.is_number_internal(destination) == True and len(destination) == 11:
						sms_log.info('SMS is for another site')
						try:
							site_ip = numbering.get_site_ip(destination)
							sms_log.info('Send SMS to site IP: %s' % site_ip)
							self.context = 'SMS_INTERNAL'
							self.send(source,destination,text,site_ip)
						except NumberingException as e:
							raise SMSException('Receive SMS error: %s' % e)
					else:
						# dest number is for an external number send sms to sms provider
						return
		except NumberingException as e:
			raise SMSException('Receive SMS Error: %s' % e)
	
	def send(self, source, destination, text, server=config['local_ip']):
		enc_text = urllib.urlencode({'text': text })
		if server == config['local_ip']:
			try:
				sms_log.info('Send SMS: %s %s %s' % (source, destination, text))
        	                res = urllib.urlopen(
                	                "http://%s:%d/cgi-bin/sendsms?username=%s&password=%s&charset=%s&coding=%s&to=%s&from=%s&%s"\
                        	        % (server, self.port, self.username, self.password, self.charset, self.coding, destination, source, enc_text)
	                        ).read()
				# save sms
				sms_log.info('Save SMS in the history')
				self.save(source,destination,self.context)
        	        except IOError:
                	        raise SMSException('Error connecting to Kannel to send SMS: %s' % e)
		else:
			try:
				sms_log.info('Send SMS to %s: %s %s %s' % (server, source, destination, text))
				values = {'source': source, 'destination': destination, 'text': text }
				res = urllib.urlopen('http://%s:8085/sms' % (server,values)).read()
				sms_log.info('Save SMS in the history')
				self.save(source,destination,self.context)
			except IOError:
				raise SMSException('Error sending SMS to site %s' % server)

				
	def save(self,source,destination,context):
		# insert SMS in the history
		try:
			cur = db_conn.cursor()
			cur.execute('INSERT INTO sms(source_addr,destination_addr,context) VALUES(%s,%s,%s)', (source,destination,context))
		except psycopg2.DatabaseError as e:
			db_conn.rollback()
			raise SMSException('PG_HLR error saving SMS in the history: %s' % e)
		finally:
			db_conn.commit()


	def send_immediate(self,num,text):
		appstring = "OpenBSC"
		appport = 4242
		vty = obscvty.VTYInteract(appstring, "127.0.0.1", appport)
		cmd = 'subscriber extension %s sms sender extension 10000 send %s' % (num,text)
		vty.command(cmd)


	
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

