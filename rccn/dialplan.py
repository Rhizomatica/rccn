############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
# Copyright (C) 2019 keith <keith@rhizomatica.org>
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
        self.local_caller_check = False

        modules = [self.subscriber, self.numbering,
                   self.billing, self.configuration]

        self.context = Context(session, modules)

    def parse_chans(self, data):
        chans = []
        lines = data.split('\n')
        for line in lines:
            if line != '' and line.find(' total.') == -1:
                values = line.split('|')
                if values[0] == 'uuid':
                    keys = values
                    continue
                chan = {}
                for i, val in enumerate(values):
                    try:
                        chan[keys[i]] = val
                    except Exception as ex:
                        log.debug(ex)
                chans.append(chan)
        return chans

    def check_chans(self, match, max, redirect=''):
        i = 0
        while self.session.ready() and i < 4:
            _count = 0
            self.session.execute("set", "_temp=${show channels as delim |}")
            # Below avoids recursive data returned due to _temp=[channels] being the
            # current application_data in this channel.
            self.session.execute("set", "_tmp=1")
            _chans = self.parse_chans(self.session.getVariable('_temp'))
            for chan in _chans:
                if chan['dest'] == match:
                    _count += 1
            log.info("Channel Usage(%s) for [%s]", _count, match)
            if _count < max:
                return True
            log.info("Channel Capacity for(%s) is exceeded.", match)
            if redirect == '':
                self.play_announcement("RESOURCE_UNAVAIL")
                self.session.hangup()
                return False
            #self.session.execute('playback', '018_ocupadas.gsm')
            self.session.execute('playback', '017_marca.gsm')
            self.session.execute('say', 'es number iterated %s' % redirect)
            i += 1
        self.session.hangup()
        return False

    def play_announcement(self, status):
        """
        Play an announcement.
        """
        ann = self.context.get_audio_file(status)
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
                self.context.destination_number = self.destination_number
                log.debug('Subscriber is registered and authorized to call')
                exectx = getattr(self.context, mycontext)
                exectx()
            else:
                self.session.setVariable('context', mycontext.upper())
                log.info('Subscriber is not registered or authorized to call')
                self.play_announcement("OUTGOING_CALL_BARRED")
                self.session.hangup('CALL_REJECTED')
        except SubscriberException as _ex:
            log.error(_ex)
            self.play_announcement("SERVICE_UNAVAILABLE")

    def caller_is_local(self):
        if self.local_caller_check:
            return self.local_caller_check
        self.local_caller_check = (self.calling_host == mncc_ip_address or
                self.numbering.is_number_sip_connected(self.session, self.calling_number))
        return self.local_caller_check

    def check_free_number(self):
        if not (isinstance(free_numbers, list) and self.destination_number in free_numbers):
            return False
        if len(self.destination_number) == 10:
            dest = self.numbering.detect_mx_short_dial(self.destination_number)
        subscriber_number = self.session.getVariable('caller_id_number')
        log.info('Call to %s is free and unrestricted.', dest)
        self.session.setVariable('billing', '0')
        self.session.setVariable('context', 'OUTBOUND')
        self.context.destination_number = dest
        try:
            caller_id = self.numbering.get_callerid(subscriber_number, dest)
        except NumberingException as ex:
            log.error(ex)
        if caller_id != None:
            log.info('Set caller id to %s', caller_id)
            self.session.setVariable('effective_caller_id_number', '%s' % caller_id)
            self.session.setVariable('effective_caller_id_name', '%s' % caller_id)
        return self.context.bridge(dest)

    def check_external(self):
        if len(self.destination_number) == 10:
            self.destination_number = self.numbering.detect_mx_short_dial(self.destination_number)
        self.session.setVariable("destination_number", self.destination_number)

        if self.numbering.is_number_intl(self.destination_number):
            log.debug('Called number is an external number '
                      'send call to OUTBOUND context')
            self.auth_context('outbound')
            return True

    def check_registered(self):
        if len(self.calling_number) != 11:
            self.play_announcement("OUTGOING_CALL_BARRED")
            self.session.hangup('CALL_REJECTED')
            return False
        if self.numbering.is_number_known(self.calling_number):
            return True
        log.info('%s is unknown to us.', self.calling_number)
        self.play_announcement("OUTGOING_CALL_BARRED")
        self.session.hangup('CALL_REJECTED')
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
        if not 'support_contact' in globals() or support_contact == '':
            log.info('Support Call but no support number :(')
            self.play_announcement("RESOURCE_UNAVAIL")
            return False
        log.info('!!Support Call (%s)', self.destination_number)
        self.session.setVariable('context', "SUPPORT")
        self.session.setVariable('destination_number', support_contact)
        self.destination_number = support_contact
        self.context.destination_number = support_contact
        return self.context.bridge(support_contact)

    def check_did(self):
        if self.calling_host == mncc_ip_address:
            return
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
            self.play_announcement("OUTGOING_CALL_BARRED")
            self.session.hangup('OUTGOING_CALL_BARRED')
            #self.session.hangup('CALL_REJECTED')
            return -1
        log.debug('Execute context INBOUND call')
        return self.context.inbound()

    def check_roaming(self):
        log.debug('Check call from(%s/%s) for roaming', self.calling_number, self.calling_host)
        if self.check_roaming_caller():
            return True
        return self.check_roaming_destination()

    def check_roaming_caller(self):
        if (self.caller_is_local() and
                self.calling_number[:6] != config['internal_prefix']): # so has to be "roaming"
            try:
                _tagged_roaming = self._n.is_number_roaming(self.calling_number)
            except NumberingException as _ex:
                log.error(_ex)
                self.play_announcement("INCOMING_CALL_BARRED")
                self.session.hangup('SERVICE_UNAVAILABLE')
                return True
            log.info('Calling number %s is roaming (%s)', self.calling_number, _tagged_roaming)
            self.context.roaming_caller()
            return True
        if (not self.caller_is_local() and
                self.calling_number[:6] == config['internal_prefix']):
            log.info('Our roaming user (%s) is calling (%s) here.', self.calling_number, self.destination_number)
            self.context.roaming_caller()

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
            self.play_announcement("SERVICE_UNAVAILABLE")
            self.session.hangup('SERVICE_UNAVAILABLE')
            return True

    def check_incoming(self):
        """
        Call coming from SIP world extension@sip.rhizomatica.org
        routed here based on prefix. roaming caller not possible.
        """
        if self.calling_host == mncc_ip_address:
            return False
        if self.numbering.is_number_webphone(self.calling_number):
            log.info("Incoming Call from Webphone")
            if self.context.check_test():
                return True
        if (isinstance(sip_central_ip_address, str) and self.calling_host == sip_central_ip_address or
                isinstance(sip_central_ip_address, list) and self.calling_host in sip_central_ip_address):
            log.info("Incoming call from SIP server")
            # TODO: Not sure about this, we also call it from check_roaming()
            if self.check_roaming_destination():
                return True
            self.context.inbound()
            return True
        # Handle Transferred DID call from Other Community
        if self.check_roaming_destination():
            return True

    def check_local(self):
        try:
            log.info('Check if called number is local')
            is_local_number = self._n.is_number_local(self.destination_number)
            is_internal_number = self._n.is_number_internal(self.calling_number)
            is_right_len = lambda num: len(num) == 11

            if is_local_number and is_right_len(self.destination_number):
                log.info('Called number is a local number')
                if not self.subscriber.is_authorized(self.destination_number, 0):
                    log.info(
                        'Destination subscriber is NOT '
                        'authorized to receive calls')
                    self.play_announcement("INCOMING_CALL_BARRED")
                    self.session.hangup('OUTGOING_CALL_BARRED')
                    return True
                if is_internal_number and is_right_len(self.calling_number):
                    log.info('INTERNAL call from another site')
                    return self.context.local()
                else:
                    log.info('Send call to LOCAL context')
                    self.auth_context('local')
                    return True
        except NumberingException as _ex:
            log.error(_ex)
            self.play_announcement("SERVICE_UNAVAILABLE")
            return False
        return False

    def check_extension(self):
        if not self.caller_is_local():
            return False
        log.debug('Check if called number is an extension')
        if self.destination_number in extensions_list:
            log.info(
                'Called number is an extension, '
                'execute extension handler')
            self.session.setVariable('context', 'EXTEN')
            extension = importlib.import_module(
                'extensions.ext_' + self.destination_number,
                'extensions')
            reload(sys.modules['extensions.ext_' + self.destination_number])
            try:
                log.debug('Exec handler')
                extension.handler(self.session)
                return True
            except ExtensionException as _ex:
                log.error(_ex)
                self.play_announcement(self.ERROR)
                return False

    def check_webphone(self):
        log.debug('Check Special Extension')
        if not 'webphone_prefix' in globals():
            return False
        if (isinstance(webphone_prefix, list) and
                self.destination_number[:5] in webphone_prefix):
            self.auth_context('webphone')
            return True
        return False

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
            self.play_announcement("SERVICE_UNAVAILABLE")
        return False

    def lookup(self):
        """
        Dialplan processing to route call to the right context
        """
        if 'reload_on_call' in globals():
            reload(sys.modules[Context.__module__])
            log.info('!!! Reloaded Context from Dialplan. !!!')

        if self.destination_number == 'emergency':
            return self.check_emergency()

        if self.destination_number[:1] == "*":
            return self.check_support()

        if ('voip_chans_max' in globals() and
            'voip_mod' in globals() and
            self.destination_number == voip_did):
            if not self.check_chans(voip_did, voip_chans_max, voip_mod(voip_did)):
                return False

        if 'free_numbers' in globals():
            ret = self.check_free_number()
            if ret:
                return ret

        ret = self.check_did()
        if ret:
            return ret

        if self.check_incoming():
            return

        if not self.check_registered():
            return False

        self.destination_number = self._n.fivetoeleven(self.calling_number, self.destination_number, log)
        self.context.destination_number = self.destination_number

        if self.check_extension():
            return
        if self.check_roaming():
            return
        if self.check_external():
            return
        ret = self.check_local()
        if ret:
            return ret
        if self.check_webphone():
            return
        if self.check_internal():
            return
        if self.context.check_test():
            return

        log.info('EOF: Unknown Number')
        self.play_announcement("UNALLOCATED_NUMBER")
        self.session.hangup('UNALLOCATED_NUMBER')
