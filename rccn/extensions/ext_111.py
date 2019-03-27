############################################################################
#
# Copyright (C) 2019 keith <keith@rhizomatica.org>
#
# Test extension to say date and time and then echo.
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
    log.debug('Handler for ext 111')
    session.answer()
    session.execute('say', 'es current_date_time pronounced foo')
    session.execute('delay_echo', '2000')
    session.hangup()
