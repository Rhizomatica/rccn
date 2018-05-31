############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
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

from config import *
from dialplan import Dialplan
from freeswitch import *

def hangup_hook(session, what):
    """ Unused hangup hook """
    return

def fsapi(session, stream, event, args):
    """ Handler when the call is hangup. used for billing """
    return

def input_callback(session, what, obj):
    if (what == "dtmf"):
        consoleLog("info", what + " " + obj.digit + "\n")
    else:
        consoleLog("info", what + " " + obj.serialize() + "\n")     
    return "pause"

def handler(session, args):
    """ Main calls handler """
    session.setVariable('billing', '0')
    destination_number = session.getVariable("destination_number")
    reload(sys.modules[Dialplan.__module__])
    dialplan = Dialplan(session)
    log.info('===========================================================================')
    log.info("HERMES Callback got a call with A-leg to: %s" % destination_number)
    dialplan.hermes_bleg()
    log.info('Leaving hermes.handler()')
    log.info('===========================================================================')
    
def xml_fetch(params):

    xml = '''
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<document type="freeswitch/xml">
  <section name="dialplan" description="RE Dial Plan For FreeSWITCH">
    <context name="default">
      <extension name="generated">
        <condition>
         <action application="answer"/>
         <action application="playback" data="${hold_music}"/>
        </condition>
      </extension>
    </context>
  </section>
</document>
'''
    return xml

