############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
# Copyright (C) 2018 keith <keith@rhizomatica.org>
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

    NOT_CREDIT_ENOUGH = '002_saldo_insuficiente.gsm'
    NOT_AUTH = '013_no_autorizado.gsm'
    NOT_REGISTERED = '015_no_access.gsm'
    WRONG_NUMBER = '007_el_numero_no_es_corecto.gsm'


    def __init__(self, session, modules):
        """ Init

        :param session: FS session
        :param modules: Array of modules instances to be used in the object
        """
        self.session = session
        self.destination_number = self.session.getVariable('destination_number')
        self.calling_number = self.session.getVariable('calling_id_number')
        self.calling_host = self.session.getVariable("sip_network_ip")

        self.subscriber = modules[0]
        self.numbering = modules[1]
        self.billing = modules[2]
        self.configuration = modules[3]

    def get_audio_file(self, disposition):
        return {
            "DESTINATION_OUT_OF_ORDER" : "008_el_numero_no_esta_disponible.gsm",
            "NO_ANSWER"                : "008_el_numero_no_esta_disponible.gsm",
            "NO_USER_RESPONSE"         : "008_el_numero_no_esta_disponible.gsm",
            "SUBSCRIBER_ABSENT"        : "008_el_numero_no_esta_disponible.gsm",
            "USER_BUSY"                : "009_el_numero_esta_ocupado.gsm",
            "UNALLOCATED_NUMBER"       : "007_el_numero_no_es_corecto.gsm",
            "NO_ROUTE_DESTINATION"     : "007_el_numero_no_es_corecto.gsm",
            "RESOURCE_UNAVAIL"         : "005_todas_las_lineas_estan_ocupadas.gsm",
            "INVALID_GATEWAY"          : "010_no_puede_ser_enlazada.gsm",
            "GATEWAY_DOWN"             : "010_no_puede_ser_enlazada.gsm",
            "CALL_REJECTED"            : "007_el_numero_no_es_corecto.gsm",
            "NORMAL_TEMPORARY_FAILURE" : "010_no_puede_ser_enlazada.gsm", # B-leg IP unreachable
            "RECOVERY_ON_TIMER_EXPIRE" : "011_no_hay_conx_a_comunidad.gsm", # Timeout
            "SERVICE_UNAVAILABLE"      : "016_oops.gsm"
        }.get(disposition, "016_oops.gsm")

    def bridge(self, callee):
        """ All calls that are progressing arrive here
            Avoids duplication of code

        :param session: FS session
        :param destination: Where we bridge the call to
        """
        mncc_codec = 'AMR'
        mncc_port = '5050'
        inter_port = '5040'
        endpoints = []
        bridge_params = ''

        def add_local_ep():
            codec = mncc_codec
            bridge_params = ',bridge_early_media=false'
            endpoint = 'sofia/internal/sip:' + str(callee) + '@' + mncc_ip_address + ':' + mncc_port
            endpoints.append("[absolute_codec_string='^^:" + codec + "'" + bridge_params + "]" + endpoint)

        def add_sip_ep():
            sip_endpoint = self.numbering.is_number_sip_connected(self.session, callee)
            if sip_endpoint:
                codec = 'PCMA:G729'
                endpoints.append("[absolute_codec_string='^^:" + codec + "'" + bridge_params + "]" + sip_endpoint)

        def add_internal_ep():
            endpoint = 'sofia/internalvpn/sip:' + str(callee) + '@' + str(site_ip) + ':' + inter_port
            bridge_params = ',bridge_early_media=true'
            codec = 'AMR:G729'
            endpoints.append("[absolute_codec_string='^^:" + codec + "'" + bridge_params + "]" + endpoint)

        self.session.execute('set', "continue_on_fail="
                             "DESTINATION_OUT_OF_ORDER,"
                             "USER_BUSY,"
                             "NO_ANSWER,"
                             "NO_ROUTE_DESTINATION,"
                             "NO_USER_RESPONSE,"
                             "UNALLOCATED_NUMBER,"
                             "INVALID_GATEWAY,"
                             "GATEWAY_DOWN,"
                             "CALL_REJECTED,"
                             "NORMAL_TEMPORARY_FAILURE,"
                             "INVALID_PROFILE,"
                             "RECOVERY_ON_TIMER_EXPIRE,"
                             "BEARERCAPABILITY_NOTIMPL,"
                             "NETWORK_OUT_OF_ORDER")

        # The default for hangup_after_bridge is false but no harm to have it here
        self.session.execute('set', 'hangup_after_bridge=false')
        #self.session.execute('set', 'fail_on_single_reject=true')
        # If we get early media, we'd ignore it.. (in case need late neg.)
        self.session.execute('set', 'ignore_early_media=false')
        # can we set the port?
        #self.session.execute('set', 'remote_media_port=60000')
        #self.session.execute('set', 'ringback=${us-ring}')

        # Defaults to sending the call to the local SIP to MNCC UA
        _context = self.session.getVariable('context')
        log.info("Bridge Context: %s", _context)
        # build an array of all possible sip endpoints, then bridge.

        if _context == 'OUTBOUND':
            """
            OUTBOUND: Call has intl destination.
            """

            ''' TODO
            try:
                codec = self.configuration.get_meta('outbound_codec')
            except ConfigurationException as e:
                log.error(e)
            '''
            codec = 'G729'
            try:
                gw = self.numbering.get_gateway()
                if gw is None:
                    log.error('Error in getting the Gateway to use for the call')
                    self.session.execute('playback', '%s' % self.get_audio_file('INVALID_GATEWAY'))
                    self.session.hangup('INVALID_GATEWAY')
                    return
                log.debug('Use gateway: %s', gw)
            except NumberingException as numex:
                log.error(numex)
                self.session.execute('playback', '%s' % self.get_audio_file('INVALID_GATEWAY'))
                return False
            endpoint = 'sofia/gateway/' + gw + '/' + str(callee)
            bridge_params = ',sip_cid_type=pid'
            endpoints.append("[absolute_codec_string='^^:" + codec + "'" + bridge_params + "]" + endpoint)

        if _context == 'ROAMING_OUTBOUND':
            """
            ROAMING_OUTBOUND: Sending the intl call from a roaming user via their home site, for billing etc.
            """
            self.session.execute('set', 'ringback=%(500,500,450,500);%(250,1000,450,500)')
            self.session.execute('set', 'instant_ringback=true')
            site_ip = self.numbering.get_site_ip(self.session.getVariable('caller_id_number'))
            add_internal_ep()

        if (_context == 'INBOUND' or _context == 'LOCAL' or
                _context == 'INTERNAL_INBOUND' or _context == "ROAMING_LOCAL" or
                _context == 'SUPPORT'):
            """
            INBOUND: Call from Voip Provider
            LOCAL: from local() to local user.
            INTERNAL_INBOUND:  call for local called number is originating another site.
            ROAMING_LOCAL: A local/internal user is calling a local/foreign user that is here.
            """
            self.session.setVariable('effective_caller_id_number', '%s' % self.session.getVariable('caller_id_number'))
            self.session.setVariable('effective_caller_id_name', '%s' % self.session.getVariable('caller_id_name'))
            self.session.execute('set', 'ringback=${us-ring}')
            #self.session.preAnswer()
            add_local_ep()
            if use_sip and not self.numbering.is_number_internal(self.destination_number):
                # Foreign user will not be (SIP) registered here.
                add_sip_ep()
            if _context == "ROAMING_LOCAL": # Also bridge to home in case our info is incorrect.
                site_ip = self.numbering.get_site_ip(self.destination_number)
                if site_ip != self.calling_host and site_ip != config['local_ip']: # But don't loop back to origin!
                    add_internal_ep()

        if (_context == 'INTERNAL' or _context == 'ROAMING_INTERNAL'
            or _context == "ROAMING_INBOUND" or _context == "ROAMING_BOTH"):
            """
            INTERNAL:           A-leg: Call to another site.
            ROAMING_INTERNAL:   A-leg: Call from a roaming user (here), is to another roaming user.
            ROAMING_BOTH:       A-leg: Call from a roaming user (here) B-leg: callee is roaming here.
            ROAMING_INBOUND:    A-leg: Call from VoIP provider to a (local) roaming user.   B-leg: local,sip,remote
            """
            try:
                site_ip = self.numbering.get_current_bts(callee)
                if site_ip == config['local_ip']:
                    site_ip = self.numbering.get_site_ip(callee)
            except NumberingException as ne:
                # FIXME: Again, we don't know if not exists or other error :(
                log.error(ne)
                self.session.execute('playback', '%s' % self.get_audio_file('UNALLOCATED_NUMBER'))
                self.session.hangup('UNALLOCATED_NUMBER')
                return

            self.session.setVariable('effective_caller_id_number', '%s' % self.session.getVariable('caller_id_number'))
            self.session.setVariable('effective_caller_id_name', '%s' % self.session.getVariable('caller_id_number'))
            self.session.execute('set', 'ringback=%(500,500,450,500);%(250,1000,450,500)')
            self.session.execute('set', 'instant_ringback=true')
            self.session.execute('set', 'bridge_early_media=true')
            self.session.execute('set', 'ignore_early_media=false')

            if _context == 'ROAMING_BOTH' or _context == 'ROAMING_INBOUND':
                self.session.execute('set', 'ringback=${us-ring}')
                add_local_ep()
                #add_sip_ep()
            if site_ip != self.calling_host and site_ip != config['local_ip']:
                # Don't bridge the call back to the origin or to our own internal profile.
                add_internal_ep()

        if _context[:8] == 'ROAMING_':
            self.session.execute('set', "continue_on_fail=true")

        # Now bridge B-leg of call.
        log.info('Bridging to (%s) EP(s):', _context)
        for ep in endpoints:
            log.info('---> \033[92;1m%s\033[0m', ep)
        bridge_str = ",".join(endpoints)
        self.session.execute('bridge', bridge_str)

        # ============== AFTER THE BRIDGE ==============

        _orig_disp = self.session.getVariable('originate_disposition')
        _ep_disp = self.session.getVariable('endpoint_disposition')
        _ctime = float(self.session.getVariable('created_time'))/1000000
        _atime = float(self.session.getVariable('answered_time'))/1000000
        # Note that if the A leg hangs up, then the last bridge hangup
        # is not from the connected B-leg.
        _hup_cause = self.session.getVariable('last_bridge_hangup_cause')

        log.info('Bridge Finished with B-leg of Call, orig_disp(%s) ep_disp(%s) hup_cause(%s)',
                 _orig_disp, _ep_disp, _hup_cause)
        if _atime > 0:
            log.info('Approx Timings, S->A(%0.2f) Duration(%0.2f)',
                     (_atime - _ctime),
                     (time.time() - _atime))

        if _orig_disp == "SUCCESS":
            if _ep_disp == "ANSWER":
                return _hup_cause
            if _ep_disp == "EARLY MEDIA":
                self.session.hangup(_hup_cause)
                if _hup_cause != "NORMAL_CLEARING":
                    return False
                else:
                    return True

        if _orig_disp == "ORIGINATOR_CANCEL":
            self.session.hangup(_orig_disp)
            return True

        if (_context != "ROAMING_LOCAL" and _context != "ROAMING_BOTH" and
            _context[:8] == "ROAMING_" and _orig_disp == "UNALLOCATED_NUMBER"):
            # Don't play audio to an incoming roaming call for a number that is
            # unknown to OsmoHLR, this would kill any another bridge.
            # Also it might not be correct.
            self.session.hangup("SUBSCRIBER_ABSENT")
            return

        if ((_context == "ROAMING_LOCAL" or _context == "ROAMING_BOTH") and
            _orig_disp == "UNALLOCATED_NUMBER"):
            log.debug("Forcing DESTINATION_OUT_OF_ORDER for UNALLOCATED_NUMBER")
            _orig_disp = "DESTINATION_OUT_OF_ORDER"
            _hup_cause = "DESTINATION_OUT_OF_ORDER"

        if (self.calling_host != mncc_ip_address and
            (_context == "INTERNAL_INBOUND" or _context == "ROAMING_INTERNAL" or
             _context == "ROAMING_LOCAL")):
            log.debug("Not playing Audio to %s", self.calling_host)
            # Let the caller side deal with audio feedback
            self.session.hangup(_hup_cause)
            return True

        if _context == "SUPPORT":
            _hup_cause = "RESOURCE_UNAVAIL"

        # Playback our own audio based on originate disposition.
        if (_orig_disp == "NORMAL_CLEARING" or _orig_disp == "DESTINATION_OUT_OF_ORDER" or
                _orig_disp == "NORMAL_TEMPORARY_FAILURE"):
            _audio_f = self.get_audio_file(_hup_cause)
        else:
            _audio_f = self.get_audio_file(_orig_disp)
        if _orig_disp == "RECOVERY_ON_TIMER_EXPIRE" and _context == "OUTBOUND":
            _audio_f = self.get_audio_file("GATEWAY_DOWN")

        log.debug('Playback to caller: <%s>', _audio_f)
        if _audio_f != "":
            #self.session.execute('info')
            self.session.execute('playback', '%s' % _audio_f)
            log.debug('Playback Finished.')
            # Don't hangup here if you want to go back into the inbound loop.
            if not _context == "INBOUND":
                self.session.hangup(_orig_disp)

    def outbound(self):
        """ Outbound context. Calls to be sent out using the VoIP provider """
        self.session.setVariable('context', 'OUTBOUND')
        subscriber_number = self.session.getVariable('caller_id_number')
        # check subscriber balance
        log.debug('Check subscriber %s balance', subscriber_number)
        try:
            current_subscriber_balance = Decimal(self.subscriber.get_balance(subscriber_number))
        except SubscriberException as _ex:
            log.error(_ex)
            self.session.execute('playback', self.NOT_CREDIT_ENOUGH)
            self.session.hangup('OUTGOING_CALL_BARRED')

        log.debug('Current subscriber balance: %.2f', current_subscriber_balance)
        if current_subscriber_balance > Decimal('0.00'):
            # subscriber has enough balance to make a call
            log.debug('Get call rate')
            self.session.setVariable('billing', '1')
            rate = self.billing.get_rate(self.destination_number)
            total_call_duration = self.billing.get_call_duration(current_subscriber_balance, rate[3])
            log.info('Total duration for the call before balance end is set to %d sec', total_call_duration)
            mid_announcement = total_call_duration - 30
            self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' %
                                 total_call_duration)
            if total_call_duration > 60:
                self.session.execute('set',
                                     'execute_on_answer_2=sched_broadcast +%s playback::003_saldo_esta_por_agotarse.gsm' %
                                     mid_announcement)
            self.session.execute('set', 'execute_on_answer_3=sched_broadcast +%s playback::004_saldo_se_ha_agotado.gsm' %
                                 (total_call_duration - 3))
            # set correct caller id based on the active provider
            try:
                outbound_codec = 'G729'
                caller_id = self.numbering.get_callerid(subscriber_number, self.destination_number)
            except NumberingException as ex:
                log.error(ex)

            if caller_id != None:
                log.info('Set caller id to %s', caller_id)
                self.session.setVariable('effective_caller_id_number', '%s' % caller_id)
                self.session.setVariable('effective_caller_id_name', '%s' % caller_id)
                self.session.execute('set', 'sip_h_P-Charge-Info=%s' % subscriber_number)
            else:
                log.error('Error getting the caller id for the call')
                self.session.setVariable('effective_caller_id_number', 'Unknown')
                self.session.setVariable('effective_caller_id_name', 'Unknown')
            self.bridge(self.destination_number)
        else:
            log.debug('Subscriber doesn\'t have enough balance to make a call')
            # play announcement not enough credit and hangup call
            self.session.execute('playback', '002_saldo_insuficiente.gsm')
            self.session.hangup()

    def local(self):
        """ Local context. Calls destined for our BSC """
        calling_number = self.session.getVariable('caller_id_number')
        if self.numbering.is_number_internal(calling_number):
            self.session.setVariable('context', 'INTERNAL_INBOUND')
        else:
            self.session.setVariable('context', 'LOCAL')
            try:
                if self.configuration.check_charge_local_calls() == 1:
                    # if local call has to be billed to local subscriber:
                    rate = self.configuration.get_charge_local_calls()
                    log.debug('Check subscriber %s balance', calling_number)
                    try:
                        current_subscriber_balance = Decimal(self.subscriber.get_balance(calling_number))
                    except SubscriberException as _ex:
                        log.error(_ex)
                        current_subscriber_balance = Decimal(0)
                    log.debug('Current subscriber balance: %.2f', current_subscriber_balance)
                    if current_subscriber_balance >= rate[0]:
                        log.info('LOCAL call will be billed at %s after %s seconds', rate[0], rate[1])
                        self.session.setVariable('billing', '1')
                    else:
                        log.debug('Subscriber doesn\'t have enough balance to make a call')
                        self.session.execute('playback', self.NOT_CREDIT_ENOUGH)
                        self.session.hangup()
                        return
            except ConfigurationException as _ex:
                log.error(_ex)

        # check if the call duration has to be limited
        try:
            limit = self.configuration.get_local_calls_limit()
            if limit != False:
                if limit[0] == 1:
                    log.info('Limit call duration to: %s seconds', limit[1])
                    self.session.execute('set', 'execute_on_answer_1=sched_hangup +%s normal_clearing both' % limit[1])
        except ConfigurationException as _ex:
            log.error(_ex)
        log.info('Take it to the Bridge..')
        self.bridge(self.destination_number)

    def inbound_ivr(self):

        self.session.answer()
        loop_count = 0
        while self.session.ready() and loop_count < 6:
            loop_count += 1
            log.debug('Playback welcome message %s', loop_count)
            log.debug('Collect DTMF to call internal number')
            _greet = "001_bienvenidos.gsm"
            _path = self.session.getVariable('sound_prefix') + '/' + _greet
            if not os.path.isfile(_path):
                log.error("!! Audio file(%s) not found!!", _path)
                _greet = "000_default.gsm"
            dest_num = self.session.playAndGetDigits(5, 11, 3, 10000, "#", _greet,
                                                     self.WRONG_NUMBER, "\\d+")
            if not self.session.ready():
                return -1
            log.debug('Collected digits: %s', dest_num)
            if len(dest_num) == 5:
                self.destination_number = config['internal_prefix'] + dest_num
            elif len(dest_num) == 11:
                self.destination_number = dest_num
            try:
                if self.subscriber.is_authorized(dest_num, 1) and (len(dest_num) == 11 or len(dest_num) == 5):
                    self._check_inbound_billing()
                    log.info('Send call to subscriber %s', self.destination_number)
                    ret = self._check_inbound_roaming()
                    if not ret:
                        ret = self.bridge(self.destination_number)
                        if not ret:
                            continue
                        else:
                            return ret
                    else:
                        return ret
                else:
                    self._play_error(self.destination_number)
            except SubscriberException as _ex:
                log.error(_ex)
                self.session.execute('playback', self.WRONG_NUMBER)
                self.session.hangup("UNALLOCATED_NUMBER")
                return -1

    def _check_inbound_billing(self):
        try:
            if self.configuration.check_charge_inbound_calls() == 1:
                log.info('INBOUND call will be billed')
                self.session.setVariable('billing', '1')
        except ConfigurationException as _ex:
            log.error(_ex)

    def _play_error(self, num):
        try:
            self.subscriber.get(config['internal_prefix'] + num)
            log.info('Subscriber %s is not authorized', num)
            self.session.execute('playback', self.NOT_AUTH)
        except SubscriberException:
            log.info('Subscriber %s doesn\'t exist.', num)
            self.session.execute('playback', self.WRONG_NUMBER)

    def _check_inbound_roaming(self):
        try:
            if self.numbering.is_number_roaming(self.destination_number):
                log.info('Inbound Called number tagged as roaming on (%s)',
                         self.numbering.get_current_bts(self.destination_number))
                self.session.setVariable('context', 'ROAMING_INBOUND')
                self.bridge(self.destination_number)
                return True
        except NumberingException as _ex:
            log.error(_ex)
            self.session.execute('playback', self.WRONG_NUMBER)
        return False

    def inbound(self):
        """ Inbound context. Calls coming from the VoIP provider """
        self.session.setVariable('context', 'INBOUND')
        subscriber_number = None
        try:
            log.info('Check if (%s) is assigned to a subscriber for direct calling',
                     self.destination_number)
            subscriber_number = self.numbering.get_did_subscriber(self.destination_number)
            if subscriber_number is None:
                log.debug('Check if Called Number is a Valid Local Subscriber Number')
                if self.numbering.is_number_local(self.destination_number):
                    subscriber_number = self.destination_number
        except NumberingException as _ex:
            log.error(_ex)

        if subscriber_number == None:
            return self.inbound_ivr()
        else:
            log.info('INBOUND call progressing to: %s', subscriber_number)
            try:
                if self.subscriber.is_authorized(subscriber_number, 1) and len(subscriber_number) == 11:
                    log.info('Send call to internal subscriber %s', subscriber_number)
                    self.session.setVariable('effective_caller_id_number', '%s' % self.session.getVariable('caller_id_number'))
                    self.session.setVariable('effective_caller_id_name', '%s' % self.session.getVariable('caller_id_name'))
                    if not self._check_inbound_roaming():
                        self.bridge(subscriber_number)
                        return True
                else:
                    log.error('DID assigned but subscriber %s does not exist or is not authorized', subscriber_number)
                    self._play_error(subscriber_number)
                    return False
            except SubscriberException as _ex:
                log.error(_ex)
                self.session.execute('playback', self.WRONG_NUMBER)
                self.session.hangup('UNALLOCATED_NUMBER')
        return -1

    def internal(self):
        """ Internal context. Calls for another site routed using internal VPN """
        self.session.setVariable('context', 'INTERNAL')
        self.bridge(self.destination_number)

    def roaming(self):
        """ Roaming context. Calls to subscribers that are currently roaming """
        try:
            site_ip = self.numbering.get_current_bts(self.destination_number)
            # if current bts is local site send call to local LCR
            # We actually do the same thing now in the bridge anyway..
            if site_ip == config['local_ip']:
                log.info('Called number is roaming on our site send call to MNCC')
                self.session.setVariable('context', 'ROAMING_LOCAL')
                self.bridge(self.destination_number)
            else:
                log.info('Called number is tagged as roaming, bridge call to location: %s', site_ip)
                self.session.setVariable('context', 'ROAMING_INTERNAL')
                self.bridge(self.destination_number)
        except NumberingException as _ex:
            log.error(_ex)

    def roaming_caller(self):

        self.destination_number = self.numbering.detect_mx_short_dial(self.destination_number)
        if self.numbering.is_number_intl(self.destination_number):
            log.info('Roaming number calls an (inter)national number.')
            calling = self.session.getVariable('caller_id_number')
            site_ip = self.numbering.get_site_ip(calling)
            if site_ip == config['local_ip']:
                #check if home_bts is same as local site, (error in roaming data)
                # if yes send call to local context outbound
                # FIXME: we should never exec this code.
                log.info('?? WTF! ?? Caller is found to be roaming on home site, send call to voip provider')
                self.outbound()
            else:
                log.info('Send call to home_bts %s of roaming user', site_ip)
                self.session.setVariable('context', 'ROAMING_OUTBOUND')
                self.bridge(self.destination_number)

        if self.numbering.is_number_roaming(self.destination_number):
            # well destination number is roaming as well, send call to the current_bts where the subscriber is roaming
            try:
                site_ip = self.numbering.get_current_bts(self.destination_number)
                log.info('Called number is roaming send call to current_bts: %s', site_ip)
                self.session.setVariable('context', 'ROAMING_INTERNAL')
                if site_ip == config['local_ip']:
                    self.session.setVariable('context', 'ROAMING_BOTH')
                self.bridge(self.destination_number)
            except NumberingException as _ex:
                log.error(_ex)
        else:
            # destination number is not roaming check if destination number is for local site
            if (len(self.destination_number) == 11 and
                    self.numbering.is_number_local(self.destination_number)):
                log.info('Called number is a local number')
                if self.subscriber.is_authorized(self.destination_number, 0):
                    # check if the call duration has to be limited
                    try:
                        limit = self.configuration.get_local_calls_limit()
                        if limit != False:
                            if limit[0] == 1:
                                log.info('Limit call duration to: %s seconds', limit[1])
                                self.session.execute('set',
                                                     'execute_on_answer_1=sched_hangup +%s normal_clearing both' % limit[1])
                    except ConfigurationException as _ex:
                        log.error(_ex)
                    log.info('Send roaming call to local MNCC')
                    self.session.setVariable('context', 'ROAMING_LOCAL')
                    self.bridge(self.destination_number)
                else:
                    self.session.execute('playback', self.NOT_AUTH)
                    self.session.hangup('OUTGOING_CALL_BARRED')
            else:
                # number is not local, check if number is internal
                if len(self.destination_number) == 11 and self.numbering.is_number_internal(self.destination_number):
                    # number is internal send call to destination site
                    try:
                        site_ip = self.numbering.get_site_ip(self.destination_number)
                        log.info('Send call to site IP: %s', site_ip)
                        self.session.setVariable('context', 'ROAMING_INTERNAL')
                        self.bridge(self.destination_number)
                    except NumberingException as _ex:
                        log.error(_ex)
                else:
                    # check if destination number is an international call
                    if self.destination_number[0] == '+' or re.search(r'^00', self.destination_number) != None:
                        return
                    else:
                        # called number must be wrong, hangup call
                        log.error("End of Dialplan with <%s> -> <%s>", self.calling_number, self.destination_number)
                        self.session.execute('playback', '%s' % self.get_audio_file('SERVICE_UNAVAILABLE'))
                        #self.session.hangup()
