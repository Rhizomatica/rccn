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
    """ Context object """

    def __init__(self, session, modules):
        """ Init
        
        :param session: FS session
        :param modules: Array of modules instances to be used in the object
        """
        self.session = session
        self.destination_number = self.session.getVariable('destination_number')
        self.calling_number = self.session.getVariable('calling_id_number')

        self.subscriber = modules[0]
        self.numbering = modules[1]
        self.billing = modules[2]
        self.configuration = modules[3]

    def outbound(self):
        """ Outbound context. Calls to be sent out using the VoIP provider """

        self.session.setVariable('context', 'OUTBOUND')
        subscriber_number = self.session.getVariable('caller_id_number')
        # check subscriber balance
        log.debug('Check subscriber %s balance' % subscriber_number)
        try:
            current_subscriber_balance = Decimal(self.subscriber.get_balance(subscriber_number))
        except SubscriberException as e:
            log.error(e)
            current_subscriber_balance = 0
            # play announcement and hangup call
            # TODO: announcement of general error

        log.debug('Current subscriber balance: %.2f' % current_subscriber_balance)
        if current_subscriber_balance > Decimal('0.00'):
            # subscriber has enough balance to make a call
            log.debug('Get call rate')
            self.session.setVariable('billing', '1')

            rate = self.billing.get_rate(self.destination_number)
            total_call_duration = self.billing.get_call_duration(current_subscriber_balance, rate[3])

            log.info('Total duration for the call before balance end is set to %d sec' % total_call_duration)

            mid_announcement = total_call_duration - 30

            self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' % total_call_duration)
            if total_call_duration > 60:
                self.session.execute('set', 'execute_on_answer_2=sched_broadcast +%s playback::003_saldo_esta_por_agotarse.gsm' % mid_announcement)
            
            self.session.execute('set', 'execute_on_answer_3=sched_broadcast +%s playback::004_saldo_se_ha_agotado.gsm' % (total_call_duration - 3))

            # set correct caller id based on the active provider
            try:
                caller_id = self.numbering.get_callerid(subscriber_number,self.destination_number)
            except NumberingException as e:
                log.error(e)

            '''
            try:
                outbound_codec = self.configuration.get_meta('outbound_codec')
            except ConfigurationException as e:
                log.error(e)
            '''
            outbound_codec = 'G729'

            if caller_id != None:
                log.info('Set caller id to %s' % caller_id)
                self.session.setVariable('effective_caller_id_number', '%s' % caller_id)
                self.session.setVariable('effective_caller_id_name', '%s' % caller_id)
                self.session.execute('set', 'sip_h_P-Charge-Info=%s' % subscriber_number)
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
                # TODO: announcement of general error
                self.session.execute('playback', '007_el_numero_no_es_corecto.gsm')
                self.session.hangup()
                
            self.session.execute('set',"continue_on_fail=USER_BUSY,INVALID_GATEWAY,GATEWAY_DOWN,CALL_REJECTED")
            self.session.execute('bridge', "{absolute_codec_string='"+outbound_codec+"',sip_cid_type=pid}sofia/gateway/"+gw+'/'+str(self.destination_number))
            _fail_cause=self.session.getVariable('originate_disposition')
            log.info('Gateway Finished with Call: %s' % _fail_cause)
            if _fail_cause == "INVALID_GATEWAY" or _fail_cause == "GATEWAY_DOWN" or _fail_cause == "CALL_REJECTED":
                self.session.execute('playback', '010_no_puede_ser_enlazada.gsm')
            if _fail_cause == "USER_BUSY":
                self.session.execute('playback', '009_el_numero_esta_ocupado.gsm')
        else:
            log.debug('Subscriber doesn\'t have enough balance to make a call')
            # play announcement not enough credit and hangup call
            self.session.answer()
            self.session.execute('playback', '002_saldo_insuficiente.gsm')
            self.session.hangup()

    def local(self):
        """ Local context. Calls within the same BSC """
        # check if calling number is internal
        calling_number = self.session.getVariable('caller_id_number')
        if self.numbering.is_number_internal(calling_number) == True:
            self.session.setVariable('context', 'INTERNAL')
        else:
            self.session.setVariable('context', 'LOCAL')
            # check if local call has to be billed
            try:
                if self.configuration.check_charge_local_calls() == 1:
                    log.debug('Check subscriber %s balance' % calling_number)
                    try:
                        current_subscriber_balance = Decimal(self.subscriber.get_balance(calling_number))
                    except SubscriberException as e:
                        log.error(e)
                        current_subscriber_balance = 0
                    log.debug('Current subscriber balance: %.2f' % current_subscriber_balance)
                    rate = self.configuration.get_charge_local_calls()
                    if current_subscriber_balance >= rate[0]:
                        log.info('LOCAL call will be billed at %s after %s seconds' % (rate[0], rate[1]))
                        self.session.setVariable('billing', '1')
                    else:
                        log.debug('Subscriber doesn\'t have enough balance to make a call')
                        self.session.execute('playback', '002_saldo_insuficiente.gsm')
                        self.session.hangup()
                        return
            except ConfigurationException as e:
                    log.error(e)
 
        # check if the call duration has to be limited
        try:
            limit = self.configuration.get_local_calls_limit()
            if limit != False:
                if limit[0] == 1:
                    log.info('Limit call duration to: %s seconds' % limit[1])
                    self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' % limit[1])
        except ConfigurationException as e:
            log.error(e)
                        
        # Experimental local calls to SIP endpoint.
        if use_sip == 'yes':
          sip_endpoint=self.numbering.is_number_sip_connected(self.session,self.destination_number)
          #sip_endpoint=self.numbering.is_number_sip_connected_no_session(self.destination_number)
          if sip_endpoint:
            self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION,UNALLOCATED_NUMBER")
            self.session.execute('bridge', "{absolute_codec_string='PCMA,G729'}"+sip_endpoint)
            _fail_cause=self.session.getVariable('originate_disposition')
            log.info('SIP Finished with Call: %s' % _fail_cause)
            return
        # check subscriber balance if charge local call is configured
        log.info('Send call to LCR')
        # Hangup after bridge is true in the dialplan.
        #self.session.execute('set','hangup_after_bridge=false')
        self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION,UNALLOCATED_NUMBER")
        self.session.execute('bridge', "{absolute_codec_string='GSM'}sofia/internal/sip:"+str(self.destination_number)+'@'+mncc_ip_address+':5050')
        _fail_cause=self.session.getVariable('originate_disposition')
        log.info('LCR Finished with Call: %s' % _fail_cause)
        if _fail_cause == "DESTINATION_OUT_OF_ORDER" or _fail_cause == "NO_ANSWER":
            self.session.execute('playback', '008_el_numero_no_esta_disponible.gsm')
        if _fail_cause == "USER_BUSY":
            self.session.execute('playback', '009_el_numero_esta_ocupado.gsm')
        if _fail_cause == "UNALLOCATED_NUMBER":
            self.session.execute('playback', '007_el_numero_no_es_corecto.gsm')            

        # in case of no answer send call to voicemail
        #log.info('No answer, send call to voicemail')
        #self.session.execute('set','default_language=en')
        #self.session.execute('answer')
        #self.session.execute('sleep','1000')
        #self.session.execute('bridge', "loopback/app=voicemail:default ${domain_name} "+str(self.calling_number))

    def inbound(self):
        """ Inbound context. Calls coming from the VoIP provider """
        self.session.setVariable('context', 'INBOUND')
        # check if DID is assigned to a subscriber
        #try:
        #    log.info('Check if DID is assigned to a subscriber for direct calling')
        #    subscriber_number = self.numbering.get_did_subscriber(self.destination_number)
        #except NumberingException as e:
        #    log.error(e)
        try:
            log.debug('Check if Number is a Valid Local Number')
            if (self.numbering.is_number_local(self.destination_number)):
                subscriber_number = self.destination_number
            else:
                subscriber_number = None
        except NumberingException as e:
            log.error(e)

        # FIXME: (soon) Remove all this code duplication from the dialplan
        if subscriber_number != None:
            log.info('DID assigned to: %s' % subscriber_number) 
            try:
                if self.subscriber.is_authorized(subscriber_number, 1) and len(subscriber_number) == 11:
                    log.info('Send call to internal subscriber %s' % subscriber_number)
                    # Experimental local calls to SIP endpoint.
                    if use_sip == 'yes':
                      sip_endpoint=self.numbering.is_number_sip_connected(self.session,self.destination_number)
                      #sip_endpoint=self.numbering.is_number_sip_connected_no_session(self.destination_number)
                      if sip_endpoint:
                        self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION,UNALLOCATED_NUMBER")
                        self.session.execute('bridge', "{absolute_codec_string='PCMA,G729,AMR'}"+sip_endpoint)
                        _fail_cause=self.session.getVariable('originate_disposition')
                        log.info('SIP Finished with Call: %s' % _fail_cause)
                        return
                    log.info('Send call to internal subscriber %s' % subscriber_number)
                    self.session.setVariable('effective_caller_id_number', '%s' % self.session.getVariable('caller_id_number'))
                    self.session.setVariable('effective_caller_id_name', '%s' % self.session.getVariable('caller_id_name'))
                    self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION")
                    self.session.execute('bridge', "{absolute_codec_string='GSM'}sofia/internal/sip:"+subscriber_number+'@'+mncc_ip_address+':5050')
                    _fail_cause=self.session.getVariable('originate_disposition')
                    log.info('LCR Finished with Call: %s' % _fail_cause)
                    if _fail_cause == "DESTINATION_OUT_OF_ORDER":
                      self.session.execute('playback', '008_el_numero_no_esta_disponible.gsm')
                    elif _fail_cause == "USER_BUSY":
                      self.session.execute('playback', '009_el_numero_esta_ocupado.gsm')
                    else:
                      self.session.hangup()

                else:
                    log.info('Subscriber %s doesn\'t exist or is not authorized' % subscriber_number)
            except SubscriberException as e:
                log.error(e)
                # internal error
                # TODO: announcement of general error
                self.session.execute('playback','007_el_numero_no_es_corecto.gsm')
        else:
            self.session.answer()
            loop_count=0
            while self.session.ready() == True and loop_count < 6:
                loop_count += 1
                log.debug('Playback welcome message %s', loop_count)
                log.debug('Collect DTMF to call internal number')
                dest_num = self.session.playAndGetDigits(5, 11, 3, 10000, "#", "001_bienvenidos.gsm", "007_el_numero_no_es_corecto.gsm", "\\d+")
                log.debug('Collected digits: %s' % dest_num)
                if self.session.ready() != True:
                    return

                # check if destination subscriber is roaming
                try:
                    if len(dest_num) == 5:
                        self.destination_number = config['internal_prefix']+dest_num
                    elif len(dest_num) == 11:
                        self.destination_number = dest_num
                    if self.numbering.is_number_roaming(self.destination_number):
                        log.info('Destination number %s is roaming' % self.destination_number)
                        self.roaming('inbound')
                except NumberingException as e:
                    log.error(e)
                    # TODO: play message of destination number unauthorized to receive call
                    self.session.hangup()

                # Experimental local calls to SIP endpoint.
                if use_sip == 'yes':
                  sip_endpoint=self.numbering.is_number_sip_connected(self.session,self.destination_number)
                  #sip_endpoint=self.numbering.is_number_sip_connected_no_session(self.destination_number)
                  if sip_endpoint:
                    self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION,UNALLOCATED_NUMBER")
                    self.session.execute('bridge', "{absolute_codec_string='PCMA,G729,AMR'}"+sip_endpoint)
                    _fail_cause=self.session.getVariable('originate_disposition')
                    log.info('SIP Finished with Call: %s' % _fail_cause)
                    return


                try:
                    if self.subscriber.is_authorized(dest_num, 1) and (len(dest_num) == 11 or len(dest_num) == 5):
                        # check if the inbound call has to be billed
                        try:
                            if self.configuration.check_charge_inbound_calls() == 1:
                                log.info('INBOUND call will be billed')
                                self.session.setVariable('billing', '1')
                        except ConfigurationException as e:
                            log.error(e)
                        # if number is extension add internal prefix
                        if len(dest_num) == 5:
                            dest_num = config['internal_prefix'] + dest_num
                        log.info('Send call to internal subscriber %s' % dest_num)
                        self.session.setVariable('effective_caller_id_number', '%s' % self.session.getVariable('caller_id_number'))
                        self.session.setVariable('effective_caller_id_name', '%s' % self.session.getVariable('caller_id_name'))
                        self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION")
                        self.session.execute('bridge', "{absolute_codec_string='GSM'}sofia/internal/sip:"+dest_num+'@'+mncc_ip_address+':5050')
                        _fail_cause=self.session.getVariable('originate_disposition')
                        log.info('LCR Finished with Call: %s' % _fail_cause)
                        if _fail_cause == "DESTINATION_OUT_OF_ORDER":
                          self.session.execute('playback', '008_el_numero_no_esta_disponible.gsm')
                        elif _fail_cause == "USER_BUSY":
                          self.session.execute('playback', '009_el_numero_esta_ocupado.gsm')
                        else:
                          self.session.hangup()
                    else:
                        log.info('Subscriber %s doesn\'t exist' % dest_num)
                        self.session.execute('playback','007_el_numero_no_es_corecto.gsm')

                except SubscriberException as e:
                    log.error(e)
                    # general error playback busy tone
                    self.session.execute('playback', '007_el_numero_no_es_corecto.gsm')
                    self.session.hangup()

    def internal(self):
        """ Internal context. Calls for another site routed using internal VPN """
        self.session.setVariable('context', 'INTERNAL')
        try:
            site_ip = self.numbering.get_site_ip(self.destination_number)
            log.info('Send call to site IP: %s' % site_ip)
            self.session.execute('bridge', str("{absolute_codec_string='G729'}sofia/internalvpn/sip:"+self.destination_number+'@'+site_ip+':5040'))
        except NumberingException as e:
            log.error(e)


    def roaming(self, roaming_subject):
        """ Roaming context. Calls from and to subscribers that are currently roaming """

        if roaming_subject == 'caller':
            # calling number is roaming
            # check if destination number is roaming as well
            if self.numbering.is_number_roaming(self.destination_number):
                # well destination number is roaming as well, send call to the current_bts where the subscriber is roaming
                try:
                    site_ip = self.numbering.get_current_bts(self.destination_number)
                    log.info('Called number is roaming send call to current_bts: %s' % site_ip)
                    self.session.setVariable('context','ROAMING_INTERNAL')
                    # if current_bts is the same as local site, send the call to the local LCR
                    if site_ip == config['local_ip']:
                        log.info('Currentbts same as local site send call to LCR')
                        self.session.execute('bridge', "{absolute_codec_string='GSM'}sofia/internal/sip:"+str(self.destination_number)+'@'+mncc_ip_address+':5050')
                    else:
                        self.session.execute('bridge', "{absolute_codec_string='GSM,G729'}sofia/internalvpn/sip:"+self.destination_number+'@'+site_ip+':5040')
                except NumberingException as e:
                    log.error(e)                
            else:
                # destination number is not roaming check if destination number is for local site
                if self.numbering.is_number_local(self.destination_number) and len(self.destination_number) == 11:
                    log.info('Called number is a local number')

                    if self.subscriber.is_authorized(self.destination_number, 0):
                        # check if the call duration has to be limited
                        try:
                            limit = self.configuration.get_local_calls_limit()
                            if limit != False:
                                if limit[0] == 1:
                                    log.info('Limit call duration to: %s seconds' % limit[1])
                                    self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' % limit[1])
                        except ConfigurationException as e:
                            log.error(e)
        
                        log.info('Send call to LCR')
                        # Need to remove duplicate code here.
                        self.session.setVariable('context','ROAMING_LOCAL')
                        self.session.execute('set',"continue_on_fail=DESTINATION_OUT_OF_ORDER,USER_BUSY,NO_ANSWER,NO_ROUTE_DESTINATION,UNALLOCATED_NUMBER")
                        self.session.execute('bridge', "{absolute_codec_string='GSM'}sofia/internal/sip:"+str(self.destination_number)+'@'+mncc_ip_address+':5050')
                        _fail_cause=self.session.getVariable('originate_disposition')
                        log.info('LCR Finished with Call: %s' % _fail_cause)
                        if _fail_cause == "DESTINATION_OUT_OF_ORDER" or _fail_cause == "NO_ANSWER":
                            self.session.execute('playback', '008_el_numero_no_esta_disponible.gsm')
                        if _fail_cause == "USER_BUSY":
                            self.session.execute('playback', '009_el_numero_esta_ocupado.gsm')
                        if _fail_cause == "UNALLOCATED_NUMBER":
                            self.session.execute('playback', '007_el_numero_no_es_corecto.gsm')
                        self.session.hangup()
                    else:
                        # local destination subscriber unauthorized
                        # TODO: play message destination unauthorized to receive call
                        self.session.hangup()
                else:
                    # number is not local, check if number is internal
                    if self.numbering.is_number_internal(self.destination_number) and len(self.destination_number) == 11:
                        # number is internal send call to destination site
                        try:
                            site_ip = self.numbering.get_site_ip(self.destination_number)
                            log.info('Send call to site IP: %s' % site_ip)
                            self.session.setVariable('context','ROAMING_INTERNAL')
                            self.session.execute('bridge', str("{absolute_codec_string='GSM,G729'}sofia/internalvpn/sip:"+self.destination_number+'@'+site_ip+':5040'))
                        except NumberingException as e:
                            log.error(e)
                    else:
                        # check if destination number is an international call
                        if self.destination_number[0] == '+' or re.search(r'^00', self.destination_number) != None:
                            log.info('Called number is an international call or national')
                            calling = self.session.getVariable('caller_id_number')
                            site_ip = self.numbering.get_site_ip(calling)
                            # check if home_bts is same as local site, if yes send call to local context outbound
                            if site_ip == config['local_ip']:
                                log.info('Caller is roaming and calling outside, send call to voip provider')
                                self.outbound()
                            else:
                                log.info('Send call to home_bts %s of roaming user' % site_ip)
                                self.session.setVariable('context','ROAMING_OUTBOUND')
                                self.session.execute('bridge', str("{absolute_codec_string='GSM,G729'}sofia/internalvpn/sip:"+self.destination_number+'@'+site_ip+':5040'))
                        else:
                            # called number must be wrong, hangup call
                            self.session.hangup()
        elif roaming_subject == 'called':
            # the destination number is roaming send call to current_bts of subscriber
            try:
                site_ip = self.numbering.get_current_bts(self.destination_number)
                # if current bts is local site send call to local LCR
                if site_ip == config['local_ip']:
                    log.info('Called number is roaming on our site send call to LCR')
                    self.session.setVariable('context','ROAMING_LOCAL')
                    self.session.execute('bridge', "{absolute_codec_string='GSM'}sofia/internal/sip:"+str(self.destination_number)+'@'+mncc_ip_address+':5050')
                else:
                    log.info('Called number is roaming, bridge call here + current_bts: %s' % site_ip)
                    self.session.setVariable('context','ROAMING_INTERNAL')
                    self.session.execute('bridge', "{absolute_codec_string='GSM,G729'} sofia/internal/sip:"+str(self.destination_number)+'@'+mncc_ip_address+':5050, sofia/internalvpn/sip:'+self.destination_number+'@'+site_ip+':5040')
            except NumberingException as e:
                log.error(e)
        elif roaming_subject == 'inbound':
                try:
                    site_ip = self.numbering.get_current_bts(self.destination_number)
                    if site_ip != config['local_ip']:
                        log.info('INBOUND Called number is roaming send call to current_bts: %s' % site_ip)
                        self.session.setVariable('context','ROAMING_INBOUND')
                        self.session.execute('bridge', "{absolute_codec_string='GSM,G729'}sofia/internalvpn/sip:"+self.destination_number+'@'+site_ip+':5040')
                except NumberingException as e:
                    log.error(e)

                
            
                    

                    
                    
                    

                


            
