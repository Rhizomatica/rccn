############################################################################
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
# Copyright (C) 2018 Keith <keith@rhizomatica.org>
#
# Extension to get Subscriber Number
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
from config import log

def handler(session):
    ''' Playback own Number to Caller '''
    log.debug('Handler for ext 100, Playback own Number to Caller')
    calling_number = session.getVariable('caller_id_number')
    session.answer()
    session.execute('playback', '014_su_numero_es.gsm')
    session.execute('say', 'es number iterated %s' % calling_number)
    session.hangup()
