############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Contexts call processing
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

from config import *

class Context:

	def __init__(self,session, modules):
		self.session = session
		self.destination_number = self.session.getVariable('destination_number')

		self.subscriber = modules[0]
		self.numbering = modules[1]
		self.billing = modules[2]
		self.configuration = modules[3]

	def outbound(self):
		self.session.setVariable('context', 'OUTBOUND')
		subscriber_number = self.session.getVariable('caller_id_number')
		destination_number = self.session.getVariable('destination_number')
		# check subscriber balance
		log.debug('Check subscriber %s balance' % subscriber_number)
		try:
			current_subscriber_balance = Decimal(self.subscriber.get_balance(subscriber_number))
		except SubscriberException as e:
			log.error(e)
			# play announcement and hangup call
			

		log.debug('Current subscriber balance: %.2f' % current_subscriber_balance)
		if current_subscriber_balance > Decimal('0.00'):
			# subscriber can make a call
			log.debug('Get call rate')
			self.session.setVariable('billing', '1')

			rate = self.billing.get_rate(destination_number)
			total_call_duration = self.billing.get_call_duration(current_subscriber_balance,rate[3])

			log.info('Total duration for the call before balance end is set to %d sec' % total_call_duration)

			mid_announcement = total_call_duration - 30

			self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' % total_call_duration)
			if total_call_duration > 60:
				self.session.execute('set', 'execute_on_answer_2=sched_broadcast +%s playback::003_saldo_esta_por_agotarse.gsm' % mid_announcement)
			
			self.session.execute('set', 'execute_on_answer_3=sched_broadcast +%s playback::004_saldo_se_ha_agotado.gsm' % (total_call_duration - 3))

			# set correct caller id based on the active provider
			try:
				caller_id = self.numbering.get_callerid()
			except NumberingException as e:
				log.error(e)

			if caller_id != None:
				#log.debug('Set caller id to %s' % caller_id)
				self.session.setVariable('effective_caller_id_number', '%s' % caller_id)
				self.session.setVariable('effective_caller_id_name', '%s' % caller_id)
			else:
				log.error('Error getting the caller id for the call')
				self.session.setVariable('effective_caller_id_number', 'Unknown')
				self.session.setVariable('effective_caller_id_name', 'Unknown')
			try:
				gw = self.numbering.get_gateway()
				if gw == None:
					log.error('Error in getting the Gateway to use for the call')
				log.debug('Use gateway: %s' % gw)
			except NumberingException as e:
				log.error(e)
				# playback error and hangup call
				self.session.execute('playback', '007_el_numero_no_es_corecto.gsm')
				self.session.hangup()
				
			#if re.search(r'^0052',destination_number) != None:
			#	log.info('Number is local strip 0052')
			#	destination_number = destination_number[5:]

			#destination_number = '0459514404014'
			# hardcoded did for now
			self.session.setVariable('effective_caller_id_number', '525541703851')
			self.session.setVariable('effective_caller_id_name', '525541703851')
			self.session.execute('bridge', "{absolute_codec_string='G729',sip_cid_type=pid}sofia/gateway/"+gw+'/'+str(destination_number))
		else:
			log.debug('Subscriber doesn\'t have enough balance to make a call')
			# play announcement not enough credit and hangup call
                	self.session.answer()
	                self.session.execute('playback','002_saldo_insuficiente.gsm')
        	        self.session.hangup()

	def local(self):
		self.session.setVariable('context', 'LOCAL')
		destination_number = self.session.getVariable('destination_number')

		# check if the call duration has to be limited
		try:
			limit = self.configuration.get_local_calls_limit()
			if limit != False:
				print limit
				if limit[0] == 1:
					log.info('Limit call duration to: %s seconds' % limit[1])
					self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' % limit[1])
		except ConfigurationException as e:
			log.error(e)
					
				
		# check subscriber balance
		# check if limit of call duration has to be applied
		log.info('Send call to LCR')
		self.session.execute('bridge', "{absolute_codec_string='PCMA'}sofia/internal/sip:"+str(self.destination_number)+'@'+config['local_ip']+':5050')

	def inbound(self):
	        self.session.setVariable('context', 'INBOUND')
		destination_number = self.session.getVariable('destination_number')
		# check if DID is assigned to a subscriber
		try:
			log.info('Check if DID is assigned to a subscriber for direct calling')
			subscriber_number = self.numbering.get_did_subscriber(destination_number)
		except NumberingException as e:
			log.error(e)

		if subscriber_number != '':
			log.info('DID assigned to: %s' % subscriber_number) 
			try:
				if self.subscriber.is_authorized(subscriber_number,1) and len(subscriber_number) == 11:
					log.info('Send call to internal subscriber %s' % subscriber_number)
        		                self.session.execute('bridge', "{absolute_codec_string='PCMA'}sofia/internal/sip:"+subscriber_number+'@'+config['local_ip']+':5050')
				else:
					log.info('Subscriber %s doesn\'t exists or is not authorized' % subscriber_number)
			except SubscriberException as e:
				log.error(e)
				# internal error
				self.session.execute('playback','007_el_numero_no_es_corecto.gsm')
		else:
			# do not answer the call if the call has already being answered
			if self.session.getVariable('inbound_loop') != 1:
				self.session.answer()
			log.debug('Playback welcome message')
			log.debug('Collect DTMF to call internal number')
			dest_num = self.session.playAndGetDigits(5, 11, 3, 10000, "#", "001_bienvenidos.gsm", "007_el_numero_no_es_corecto.gsm", "\\d+")
			log.debug('Collecting digits: %s' % dest_num)
			try:
				if self.subscriber.is_authorized(dest_num,1) and (len(dest_num) == 11 or len(dest_num) == 5):
					# check if the inbound call has to be billed
					try:
						if self.configuration.check_charge_inbound_calls() == 1:
							log.info('INBOUND call will be billed')
							self.session.setVariable('billing', '1')
					except ConfigurationException as e:
						log.error(e)
					
					# if number is extension add internal prefix
					if len(dest_num) == 5:
						dest_num = config['internal_prefix']+dest_num
					log.info('Send call to internal subscriber %s' % dest_num)
					self.session.setVariable('effective_caller_id_number', '%s' % self.session.getVariable('caller_id_number'))
        	                        self.session.setVariable('effective_caller_id_name', '%s' % self.session.getVariable('caller_id_name'))
	
					self.session.execute('bridge', "{absolute_codec_string='PCMA'}sofia/internal/sip:"+dest_num+'@'+config['local_ip']+':5050')
				else:
					log.info('Subscriber %s doesn\'t exists' % dest_num)
					self.session.execute('playback','007_el_numero_no_es_corecto.gsm')
					self.session.setVariable('inbound_loop','1')
					#self.inbound()
			except SubscriberException as e:
				log.error(e)
				# general error playback busy tone
				self.session.execute('playback','007_el_numero_no_es_corecto.gsm')
				self.session.hangup()

	def internal(self):
		return
