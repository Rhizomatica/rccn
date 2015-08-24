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
    WRONG_NUMBER = '007_el_numero_no_es_corecto.gsm'

    def __init__(self, session):
        """ init """
        self.session = session

        self.destination_number = self.session.getVariable(
            'destination_number')
        self.calling_number = self.session.getVariable('caller_id_number')

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
        self.session.answer()
        self.session.execute('playback', '%s' % ann)
        self.session.hangup()

    def auth_context(self, mycontext):
        """
        Authenticate subscriber before route call to context

        :param mycontext: The context to route the call to
        """
        # check if the subscriber is authorized to
        # make calls before sending the call to the context
        log.debug(
            'Check if subscriber %s is registered and authorized'
            % self.calling_number)
        try:
            if self.subscriber.is_authorized(self.calling_number, 0):
                log.debug('Subscriber is registered and authorized to call')
                exectx = getattr(self.context, mycontext)
                exectx()
            else:
                self.session.setVariable('context', mycontext.upper())
                log.info('Subscriber is not registered or authorized to call')
                # subscriber not authorized to call
                # TODO: register announcement of subscriber
                # not authorized to call
                self.play_announcement(self.NOT_CREDIT_ENOUGH)
        except SubscriberException as e:
            log.error(e)
            # play announcement error
            # TODO: register announcement of general error
            self.play_announcement(self.NOT_CREDIT_ENOUGH)

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
                        dial_str += 'sofia/internal/sip:'+emg+'@172.16.0.1:5050'
                    else:
                        dial_str += 'sofia/internal/sip:'+emg+'@172.16.0.1:5050,'
            else:
                dial_str = 'sofia/internal/sip:'+emergency_contact+'@172.16.0.1:5050'
            
            self.session.setVariable('context','EMERGENCY')
            self.session.execute('bridge', "{absolute_codec_string='GSM'}"+dial_str)
            
        # check if destination number is an incoming call
        # lookup dest number in DID table.
        if processed == 0:
            try:
                if (self._n.is_number_did(self.destination_number)):
                    log.info('Called number is a DID')
                    log.debug('Execute context INBOUND call')
                    processed = 1
                    # send call to IVR execute context
                    self.session.setVariable('inbound_loop', '0')
                    self.context.inbound()
            except NumberingException as e:
                log.error(e)

            # check if calling number or destination number is a roaming subscriber
            log.info('Check if calling/called number is roaming')
            try:
                if (self._n.is_number_roaming(self.calling_number)):
                    processed = 1
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
                        'Destination number %s is roaming'
                        % self.destination_number)
                    self.context.roaming('called')
            except NumberingException as e:
                log.error(e)
                # TODO: play message of destination number
                # unauthorized to receive call
                self.session.hangup()

            # check if destination number is an international call.
            # prefix with + or 00
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
                is_local_number = self._n.is_number_local(dest)
                is_right_len = lambda num: len(num) == 11

                if is_local_number and is_right_len(dest):
                    log.info('Called number is a local number')
                    processed = 1
                    # check if calling number is another site

                    callin = self.calling_number
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
                            # self.play_announcement(
                            # '002_saldo_insuficiente.gsm')
                            self.session.hangup()
                    else:
                        if self.subscriber.is_authorized(dest, 0):
                            log.info('Send call to LOCAL context')
                            self.auth_context('local')
                        else:
                            log.info(
                                'Destination subscriber is '
                                'unauthorized to receive calls')
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
            except NumberingException as e:
                log.error(e)
