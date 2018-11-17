#!/usr/bin/env python
############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2018 keith <keith@rhizomatica.org>
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
"""
Rhizomatica RCCN Interactive Python Shell
"""

from config import *
import code
import atexit
import readline
import rlcompleter

historyPath = os.path.expanduser("~/.pyhistory")

def save_history(historyPath=historyPath):
    import readline
    readline.write_history_file(historyPath)

if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

readline.parse_and_bind("tab: complete")
atexit.register(save_history)
del atexit, readline, save_history, historyPath

num = Numbering()
sms = SMS()
sub = Subscriber()
subs = Subscription(subscription_log)

print '-------\n\n - Welcome to the RCCN Shell\n - [TAB] completes\n'
print ''' - Available modules:\n
      num: Numbering
      sms: SMS
      sub: Subscriber
      subs: Subscription'''
print '\n-------\n'
code.interact(local=dict(globals(), **locals()))
