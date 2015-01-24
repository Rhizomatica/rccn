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
rhizomatica inactive purger
"""

from config import *

DAYS_INACTIVE = 7


def purge_inactive_subscribers():
    """
    Purge all subscribers inactive for more than
    DAYS_INACTIVE
    """
    sub = Subscriber()
    try:
        inactive = sub.get_all_inactive_since(DAYS_INACTIVE)
    except SubscriberException as e:
        purger_log.error(
            "An error ocurred getting the list of inactive: %s" % e)
        return

    for msisdn in inactive:
        try:
            if msisdn != 10000:
                sub.purge(msisdn)
                purger_log.info("Subscriber %s purged" % msisdn)
        except SubscriberException as e:
            purger_log.error("An error ocurred on %s purge: %s" % (msisdn, e))


if __name__ == '__main__':
    purge_inactive_subscribers()
