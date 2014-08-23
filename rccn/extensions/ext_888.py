############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
#
# Extension to get Subscriber balance
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

def handler(session, *args):
    log.debug('Handler for ext 888')
    calling_number = session.getVariable('caller_id_number')
    sms = SMS()
    try:
        sub = Subscriber()
        current_subscriber_balance = sub.get_balance(calling_number)
    except SubscriberException as e:
        log.error('Calling number %s unauthorized' % calling_number)
        sms.send(config['smsc'], calling_number, config['sms_source_unauthorized'])
        raise ExtensionException(e)

    session.answer()
    session.execute('playback', '006_mensaje_saldo_actual.gsm')
    text = 'Su saldo actual es de %s pesos' % current_subscriber_balance
    log.info('Send SMS to %s: %s' % (calling_number, text))
    sms.send(config['smsc'], calling_number, text)
    session.hangup()
