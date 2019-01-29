############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Dialplan call routing
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
from context import Context

class Dialplan:
    """
    Logic to assign the call to the right context
    """
    NOT_CREDIT_ENOUGH = '002_saldo_insuficiente.gsm'
    NOT_AUTH = '013_no_autorizado.gsm'
    NOT_REGISTERED = '015_no_access.gsm'
    WRONG_NUMBER = '007_el_numero_no_es_corecto.gsm'
    ERROR = '016_oops.gsm'

    def __init__(self, session):
        """ init """
        self.session = session
        self.destination_number = self.session.getVariable(
            'destination_number')
        self.calling_number = self.session.getVariable('caller_id_number')
        self.calling_host = self.session.getVariable("sip_network_ip")

        self.subscriber = Subscriber()
        self.numbering = Numbering()
        self._n = self.numbering
        self.billing = Billing()
        self.configuration = Configuration()

        modules = [self.subscriber, self.numbering,
                   self.billing, self.configuration]

        self.context = Context(session, modules)

    def play_announcement(self, ann):
        """
        Play an announcement and hangup call.

        :param ann: Filename of the announcement to be played
        :type ann: str
        """
        self.session.execute('playback', '%s' % ann)

    def auth_context(self, mycontext):
        """
        Authenticate subscriber before route call to context

        :param mycontext: The context to route the call to
        """
        log.debug('Check if subscriber %s is registered and authorized',
                  self.calling_number)
        try:
            if self.subscriber.is_authorized(self.calling_number, 0):
                log.debug('Subscriber is registered and authorized to call')
                exectx = getattr(self.context, mycontext)
                exectx()
            else:
                self.session.setVariable('context', mycontext.upper())
                log.info('Subscriber is not registered or authorized to call')
                self.play_announcement(self.NOT_REGISTERED)
                self.session.hangup('CALL_REJECTED')
        except SubscriberException as e:
            log.error(e)
            # play announcement error
            # TODO: register announcement of general error
            self.play_announcement(self.NOT_CREDIT_ENOUGH)

    def check_external(self):
        self.destination_number = self.numbering.detect_mx_short_dial(self.destination_number)
        self.session.setVariable("destination_number", self.destination_number)

        if self.numbering.is_number_intl(self.destination_number):
            log.debug('Called number is an external number '
                      'send call to OUTBOUND context')
            self.auth_context('outbound')
            return True

    def check_registered(self):
        if len(self.calling_number) != 11:
            self.play_announcement(self.NOT_REGISTERED)
            self.session.hangup('CALL_REJECTED')
            return False
        if self.numbering.is_number_known(self.calling_number):
            return True
        return False

    def check_emergency(self):
        if emergency_contact == '':
            log.info('!Emergency call but no emergency contact!')
            return False
        log.info('Emergency call send call to emergency contact %s',
                 emergency_contact)

        # check if emergency_contacts is a list of numbers
        dial_str = ''
        if ',' in emergency_contact:
            emg_numbers = emergency_contact.split(',')
            last = emg_numbers[-1]
            for emg in emg_numbers:
                if emg == last:
                    dial_str += 'sofia/internal/sip:'+emg+'@'+mncc_ip_address+':5050'
                else:
                    dial_str += 'sofia/internal/sip:'+emg+'@'+mncc_ip_address+':5050,'
        else:
            dial_str = 'sofia/internal/sip:'+emergency_contact+'@'+mncc_ip_address+':5050'

        self.session.setVariable('context', 'EMERGENCY')
        # FIXME: codec? non mncc option?
        self.session.execute('bridge', "{absolute_codec_string='GSM'}"+dial_str)
        return True

    def check_support(self):
        if not 'support_contact' in globals():
            log.info('Support Call but no support number :(')
            return False
        log.info('!!Support Call (%s)', self.destination_number)
        self.session.setVariable('context', "SUPPORT")
        self.session.setVariable('destination_number', support_contact)
        self.destination_number = support_contact
        self.context.destination_number = support_contact
        return self.context.bridge(support_contact)

    def check_did(self):
        if self.calling_host == mncc_ip_address:
            return False
        try:
            if not self._n.is_number_did(self.destination_number):
                return False
        except NumberingException as _ex:
            log.error(_ex)
            return -1
        log.info('Called number is a DID')
        log.info("Caller from: %s", self.calling_host)
        if self.calling_host == mncc_ip_address:
            log.info("Call to DID from GSM side.")
            self.play_announcement(self.NOT_AUTH)
            self.session.hangup('OUTGOING_CALL_BARRED')
            return -1
        log.debug('Execute context INBOUND call')
        self.session.setVariable('inbound_loop', '0')
        return self.context.inbound()

    def check_roaming(self):
        log.debug('Check call from(%s/%s) for roaming', self.calling_number, self.calling_host)
        if self.check_roaming_caller():
            return True
        return self.check_roaming_destination()

    def check_roaming_caller(self):
        if (self.calling_host == mncc_ip_address and # CALLER is LOCAL
                self.calling_number[:6] != config['internal_prefix']): # so has to be "roaming"
            try:
                _tagged_roaming = self._n.is_number_roaming(self.calling_number)
            except NumberingException as _ex:
                log.error(_ex)
                self.play_announcement(self.NOT_AUTH)
                self.session.hangup('SERVICE_UNAVAILABLE')
                return True
            log.info('Calling number %s is roaming (%s)', self.calling_number, _tagged_roaming)
            self.context.roaming_caller()
            return True

    def check_roaming_destination(self):
        try:
            _tagged_roaming = self._n.is_number_roaming(self.destination_number)
            if (self.calling_host != mncc_ip_address and
                    self.destination_number[:6] != config['internal_prefix'] and
                    self._n.is_number_known(self.destination_number)):
                log.info('Incoming call to Foreign destination: %s', self.destination_number)
                self.context.roaming()
                return True
            if _tagged_roaming:
                log.info('Local origin call to Roaming destination: %s', self.destination_number)
                self.context.roaming()
                return True
        except NumberingException as _ex:
            # FIXME: note difference between exception for unauth and other.
            log.error(_ex)
            self.play_announcement(self.ERROR)
            self.session.hangup('SERVICE_UNAVAILABLE')
            return True

    def check_incoming(self):
        """
        Call coming from SIP world extension@sip.rhizomatica.org
        routed here based on prefix. roaming caller not possible.
        """
        if self.calling_host == mncc_ip_address:
            return False
        if (isinstance(sip_central_ip_address,str) and self.calling_host == sip_central_ip_address or
                isinstance(sip_central_ip_address,list) and self.calling_host in sip_central_ip_address):
            log.info("Incoming call from SIP server")
            if self.check_roaming_destination():
                return True
            self.context.local()
            return True

    def check_local(self):
        try:
            log.info('Check if called number is local')
            is_local_number = self._n.is_number_local(self.destination_number)
            is_internal_number = self._n.is_number_internal(self.calling_number)
            is_right_len = lambda num: len(num) == 11

            if is_local_number and is_right_len(self.destination_number):
                log.info('Called number is a local number')
                self.context.destination_number = self.destination_number
                if not self.subscriber.is_authorized(self.destination_number, 0):
                    log.info(
                        'Destination subscriber is NOT '
                        'authorized to receive calls')
                    self.play_announcement(self.NOT_AUTH)
                    self.session.hangup('OUTGOING_CALL_BARRED')
                    return True
                if is_internal_number and is_right_len(self.calling_number):
                    log.info('INTERNAL call from another site')
                    self.context.local()
                    return True
                else:
                    log.info('Send call to LOCAL context')
                    self.auth_context('local')
                    return True
        except NumberingException as _ex:
            log.error(_ex)
            self.play_announcement(self.ERROR)
            return False
        return False

    def check_extension(self):
        log.debug('Check if called number is an extension')
        if self.destination_number in extensions_list:
            log.info(
                'Called number is an extension, '
                'execute extension handler')
            self.session.setVariable('context', 'EXTEN')
            extension = importlib.import_module(
                'extensions.ext_' + self.destination_number,
                'extensions')
            try:
                log.debug('Exec handler')
                extension.handler(self.session)
                return True
            except ExtensionException as _ex:
                log.error(_ex)
                self.play_announcement(self.ERROR)

    def check_internal(self):
        try:
            log.debug('Check if called number is a full '
                      'number for another site')
            if self._n.is_number_internal(self.destination_number):
                log.info(
                    'Called number seems to be for another site send call to '
                    'INTERNAL context')
                self.auth_context('internal')
                return True
        except NumberingException as _ex:
            log.error(_ex)
            self.play_announcement(self.ERROR)
        return False

    def lookup(self):
        """
        Dialplan processing to route call to the right context
        """
        # TODO split this monster function.
        # the processing is async we need a flag
        processed = 0

        # emergency call check
        if emergency_contact != '' and self.destination_number == 'emergency':
            log.info(
                    'Emergency call send call to emergency contact %s'
                    % emergency_contact)
            processed = 1
            # check if emergency_contacts is a list of numbers
            dial_str = ''
            if ',' in emergency_contact:
                emg_numbers = emergency_contact.split(',')
                last = emg_numbers[-1]
                for emg in emg_numbers:
                    if emg == last:
                        dial_str += 'sofia/internal/sip:'+emg+'@'+mncc_ip_address+':5050'
                    else:
                        dial_str += 'sofia/internal/sip:'+emg+'@'+mncc_ip_address+':5050,'
            else:
                dial_str = 'sofia/internal/sip:'+emergency_contact+'@'+mncc_ip_address+':5050'
            
            self.session.setVariable('context','EMERGENCY')
            self.session.execute('bridge', "{absolute_codec_string='GSM'}"+dial_str)

        if self.destination_number[:1] == "*" and 'support_contact' in vars():
            log.info('Support Call (%s)' % self.destination_number)
            self.session.setVariable('destination_number', support_contact)
            self.destination_number = support_contact
            self.context.destination_number = support_contact
            
        if processed == 0:
            # check if destination number is an incoming call
            # lookup dest number in DID table.
            try:
                if (self._n.is_number_did(self.destination_number)):
                    log.info('Called number is a DID')
                    log.info("Caller from: %s" % self.calling_host)
                    if self.calling_host == mncc_ip_address:
                        log.info("Call to DID has local origin!")
                        self.play_announcement(self.WRONG_NUMBER)
                        return
                    log.debug('Execute context INBOUND call')
                    processed = 1
                    # send call to IVR execute context
                    self.session.setVariable('inbound_loop', '0')
                    self.context.inbound()
                    return
                if (self.calling_host == sip_central_ip_address or 
                   self.calling_host == "10.23.0.20" or
                   self.calling_host == "10.23.0.21"):
                    log.info("Incoming call from SIP server")
                    processed = 1
                    self.context.inbound()
            except NumberingException as e:
                log.error(e)

            # check if calling number or destination number is a roaming subscriber
            log.info('Check if calling/called number is roaming')
            try:
                self._n.calling_host = self.calling_host
                if (self._n.is_number_roaming(self.calling_number)):
                    processed = 1
                    # Even if we are local and local by originating ip, but hlr says roaming..
                    log.info('Calling number %s is roaming' % self.calling_number)
                    self.context.roaming('caller')
            except NumberingException as e:
                log.error(e)
                # TODO: play message of calling number is not authorized to call
                self.session.hangup()

            try:
                if (self._n.is_number_roaming(self.destination_number)):
                    processed = 1
                    log.info(
                        'Destination number %s may be roaming'
                        % self.destination_number)
                    self.context.roaming('called')
            except NumberingException as e:
                log.error(e)
                # TODO: play message of destination number
                # unauthorized to receive call
                self.session.hangup()

            # check if destination number is an international call.
            # prefix with + or 00

            try:
                if (len(self.destination_number) == 10 and re.search(r'^(00|\+)', self.destination_number) is None):
                    if self.numbering.is_number_mxcel(self.destination_number):
                        self.destination_number = '00521' + self.destination_number
                    else:
                        self.destination_number = '0052' + self.destination_number
                    self.session.setVariable("destination_number", self.destination_number)
                    self.context.destination_number = self.destination_number
                    log.info('Translated dialled 10 digit number to %s' % self.destination_number)
            except NumberingException as e:
                log.error(e)

            if (
                self.destination_number[0] == '+' or (
                re.search(r'^00', self.destination_number) is not None)
            ) and processed == 0:
                log.debug('Called number is an international call or national')
                processed = 1
                log.debug(
                    'Called number is an external number '
                    'send call to OUTBOUND context')
                self.auth_context('outbound')

        if processed == 0:
            try:
                log.info('Check if called number is local')
                dest = self.destination_number
                callin = self.calling_number
                if len(dest) == 5 and len(callin) == 11:
                    dest = callin[:6] + dest
                    self.context.destination_number = dest
                log.info('dest: %s' % self.destination_number)
                is_local_number = self._n.is_number_local(dest)
                is_right_len = lambda num: len(num) == 11

                if is_local_number and is_right_len(dest):
                    log.info('Called number is a local number')
                    processed = 1
                    # check if calling number is another site
                    is_internal_number = self._n.is_number_internal(callin)
                    if is_internal_number and is_right_len(callin):

                        # check if dest number is authorized to receive call
                        # if self.subscriber.is_authorized(
                        # self.calling_number,0):
                        log.info('INTERNAL call from another site')
                        if self.subscriber.is_authorized(dest, 0):
                            log.info(
                                'Internal call send number to LOCAL context')
                            self.context.local()
                        else:
                            log.info(
                                'Destination subscriber is '
                                'unauthorized to receive calls')
                            self.play_announcement('007_el_numero_no_es_corecto.gsm')
                            self.session.hangup()
                    else:
                        if self.subscriber.is_authorized(dest, 0):
                            log.info('Send call to LOCAL context')
                            self.auth_context('local')
                        else:
                            log.info(
                                'Destination subscriber is '
                                'unauthorized to receive calls')
                            self.play_announcement('007_el_numero_no_es_corecto.gsm')
                            self.session.hangup()
                else:
                    # check if called number is an extension
                    log.debug('Check if called number is an extension')
                    if self.destination_number in extensions_list:
                        processed = 1
                        log.info(
                            'Called number is an extension, '
                            'execute extension handler')
                        self.session.setVariable('context', 'EXTEN')
                        extension = importlib.import_module(
                            'extensions.ext_' + self.destination_number,
                            'extensions')
                        try:
                            log.debug('Exec handler')
                            extension.handler(self.session)
                        except ExtensionException as e:
                            log.error(e)
                    else:
                        log.debug(
                            'Check if called number is a full '
                            'number for another site'
                        )
                        is_internal_number = self._n.is_number_internal(dest)
                        if is_internal_number and is_right_len(dest):
                            log.info(
                                'Called number is a full number '
                                'for another site send call to '
                                'INTERNAL context')
                            processed = 1
                            self.auth_context('internal')
                        else:
                            # the number called must be wrong
                            # play announcement wrong number
                            log.info(
                                'Wrong number, play announcement of '
                                'invalid number format')
                            processed = 1
                            self.play_announcement(self.WRONG_NUMBER)
                            self.session.hangup('UNALLOCATED_NUMBER')
            except NumberingException as e:
                log.error(e)
                self.play_announcement('005_todas_las_lineas_estan_ocupadas.gsm')
