############################################################################
#
# Copyright (C) 2014 tele <tele@rhizomatica.org>
#
# Subscription Checker
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
"""
Rhizomatica Subscription Checker.
"""
import sys
from config import *

if len(sys.argv) > 2:
    print 'RCCN Subscription Checker\n'
    print 'Usage: %s [notice|reminder|deactivate]' % sys.argv[0]
    sys.exit(1)

action = sys.argv[1]

rsc = Subscription(subscription_log)

if action == 'notice':
    subscription_log.info(
        'Send notification to all subscribers to pay the subscription fee')
    try:
        totalsub = rsc.update_subscriptions(0)
        subscription_log.info(
            'Updated subscription status to unpaid '
            'for %d subscribers' % totalsub)
        subscription_log.info(
            'Send SMS of paying the subscription fee to all subscribers')
        rsc.send_subscription_fee_notice(notice_msg)
    except SubscriptionException as e:
        subscription_log.error('%s' % e)
elif action == 'reminder':
    subscription_log.info(
        'Send reminder to all subscribers that '
        'haven\'t yet paid the subscription')
    try:
        rsc.send_subscription_fee_reminder(reminder_msg)
    except SubscriptionException as e:
        subscription_log.error('%s' % e)
elif action == 'deactivate':
    subscription_log.info(
        'Deactivate all subscribers that '
        'haven\'t paid their subscription fee')
    try:
        rsc.deactivate_subscriptions(deactivate_msg)
    except SubscriptionException as e:
        subscription_log.error('%s' % e)
else:
    subscription_log.info('Invalid option')
    sys.exit(1)
