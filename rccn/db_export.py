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

from optparse import OptionParser
from config import *
from modules import maint

maint = maint.Maintenance()

parser = OptionParser()
parser.add_option("-t", "--table", dest="table",
                  help="Table to operate on")
parser.add_option("-s", "--start", dest="start",
                  help="Start Year")
parser.add_option("-m", "--month", dest="month",
                  help="Start Month")
parser.add_option("-n", "--numbermonths", dest="numbermonths",
                  help="Number of months from start month to archive")
parser.add_option("-x", "--status", dest="status", action="store_true",
                  help="Show status")

(options, args) = parser.parse_args()

if options.status:
    maint.get_state()
    sys.exit(True)

if options.table and options.start and options.month and options.numbermonths:
    if not maint.check_archive_dir():
        print "Problem with archive directory."
        sys.exit(False)
    if not maint.create_check_archive_table(options.table):
        print "Problem with Archive Table."
        sys.exit(False)
    if not maint.move_to_archive(options.table, options.start, options.month, options.numbermonths):
        print "Failed."
        sys.exit(False)
    sys.exit(True)

parser.print_usage()
