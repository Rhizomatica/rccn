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

from config import *

def update_foreign_subscribers():
    sub = Subscriber()
    try:
        unregistered = sub.get_all_unregistered()
        update_list(unregistered, True)
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of unregistered: %s" % e)

    try:
        foreign = sub.get_all_foreign()
        update_list(foreign)
    except SubscriberException as e:
        roaming_log.error("An error ocurred getting the list of unregistered: %s" % e)


def update_list(subscribers, welcome=False):
    numbering = Numbering()
    sub = Subscriber()
    for msisdn,imsi in subscribers:
        try:
            number =  numbering.get_msisdn_from_imsi(imsi)
            sub.update(msisdn, "roaming number", number)

            if welcome:
                send_welcome_sms(number)
            roaming_log.info("Subscriber %s in roaming" % number)

        except NumberingException as e:
            roaming_log.debug("Couldn't retrieve msisdn from the imsi: %s" % e)
        except SubscriberException as e:
            roaming_log.error("An error ocurred adding the roaming number %s: %s" % (number, e))

def send_welcome_sms(number):
    try:
        sms = SMS()
        sms.send(smsc_shortcode, number, sms_welcome_roaming)
    except SMSException as e:
        roaming_log.error("An error ocurred sending welcome sms to %s: %s" % (number, e))

def update_local_subscribers():
    sub = Subscriber()
    subscribers = sub.get_all_roaming()
    for imsi in subscribers:
        try:
            msisdn = sub.get_local_msisdn(imsi)
        except SubscriberException as e:
            roaming_log.info("Couldn't retrieve the msisdn from imsi %s: %s" % (imsi, e))
            continue
        try:
            sub.update_location(imsi, msisdn)
        except SubscriberException as e:
            roaming_log.error("An error ocurred updating the location of %s: %s" % (imsi, e))

if __name__ == '__main__':
    update_foreign_subscribers()
    update_local_subscribers()
