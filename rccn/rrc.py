############################################################################
#
# Copyright (C) 2014 Ruben Pollan <meskio@sindominio.net>
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
rhizomatica roaming checker
"""

import sys

from modules.subscriber import Subscriber, SubscriberException
from modules.numbering import Numbering, NumberingException
from confing import roaming_log

def update_foreign_subscribers():
    numbering = Numbering()
    sub = Subscriber()
    try:
        unregistered = sub.get_all_unregistered()
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of unregistered: %s" % e)
        return

    for msisdn,imsi in unregistered:
        try:
            number =  numbering.get_msisdn_from_imsi(imsi)
            sub.update(msisdn, "roaming number", number)
        except NumberingException as e:
            roaming_log.debug("Couldn't retrieve msisdn from the imsi: %s" % e)
        except SubscriberException as e:
            roaming_log.error("An error ocurred adding the roaming number %s: %s" % (number, e))

def update_local_subscribers():
    sub = Subscriber()
    subscribers = sub.get_all_roaming()
    for msisdn,imsi in subscribers:
        try:
            if sub.is_online(msisdn):
                sub.update_location(imsi, msisdn)
        except SubscriberException as e:
            roaming_log.error("An error ocurred updating the location of %s: %s" % (msisdn, e))

if __name__ == '__main__':
    update_foreign_subscribers()
    update_local_subscribers()
