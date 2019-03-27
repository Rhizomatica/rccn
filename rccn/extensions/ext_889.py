############################################################################
#
# Copyright (C) 2019 keith <keith@rhizomatica.org>
#
# Extension to speak Subscriber balance
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
    log.debug('Handler for ext 889')
    calling_number = session.getVariable('caller_id_number')
    sms = SMS()
    try:
        sub = Subscriber()
        current_subscriber_balance = sub.get_balance(calling_number)
    except SubscriberException as e:
        log.error('Calling number %s unauthorized' % calling_number)
        session.execute('playback', '016_oops.gsm')
        raise ExtensionException(e)

    session.answer()
    session.execute('playback', '012_su_saldo_es.gsm')
    session.execute('say', 'es_MX CURRENCY PRONOUNCED %s' % current_subscriber_balance)
    session.hangup()
