############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2020 matt9j <matt9j@cs.washington.edu>
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

""" This module contains adaptors to interface with the osmohlr vty and db
"""

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from osmopy import obscvty
import logging
import sqlite3

log = logging.getLogger(__name__)


class OsmoHlrError(Exception):
    pass


class OsmoHlr(object):
    """Encapsulates low-level HLR transactions with an internal interface

    The osmohlr db is not a stable interface, so updates may have to made to
    support changes to the db structure over time.

    The VTY itself is also not a stable interface, so changes and updates may
    need to happen here with new released versions of the HLR.
    """

    def __init__(self, ip_address, ctrl_port, vty_port, hlr_db_path):
        self.hlr_db_path = hlr_db_path
        self._appstring = "OsmoHLR"
        self._ip = ip_address
        self._vty_port = vty_port
        self._vty = obscvty
        # Do not access directly, use the _get_vty_connection(self) method
        self._cached_vty = None

    def get_msisdn_from_imsi(self, imsi):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute(
                "SELECT msisdn FROM subscriber WHERE imsi=?",
                [imsi]
            )
            connected = sq_hlr_cursor.fetchall()
            if len(connected) == 0:
                raise OsmoHlrError('imsi %s not found' % imsi)
            if len(connected) > 1:
                log.critical("Multiple msisdn entries share imsi %s : %s", imsi, connected)

            return connected[0][0]
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        except TypeError as e:
            raise OsmoHlrError('SQ_HLR error: number not found')
        finally:
            sq_hlr.close()

    def get_imsi_from_msisdn(self, msisdn):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('SELECT imsi from subscriber WHERE msisdn=?', [msisdn])
            imsi = sq_hlr_cursor.fetchone()
            if imsi is not None:
                imsi = imsi[0]
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

        return imsi

    def get_msisdn_from_imei(self, imei):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sql = ('SELECT subscriber.imei, subscriber.imsi, '
                   'subscriber.msisdn, Subscriber.last_lu_seen '
                   'FROM subscriber '
                   'WHERE subscriber.imei=? '
                   'ORDER BY subscriber.last_lu_seen DESC LIMIT 1;')
            sq_hlr_cursor.execute(sql, [imei])
            extensions = sq_hlr_cursor.fetchall()
            return extensions
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_all_5digit_msisdns(self):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT id, msisdn FROM subscriber WHERE length(msisdn) = 5 ")
            msisdns = sq_hlr_cursor.fetchall()
            return msisdns
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_all_11digit_last_location_updates(self):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT msisdn, last_lu_seen FROM subscriber WHERE length(msisdn) = 11 ")
            result_tuples = sq_hlr_cursor.fetchall()
            result_mapping = {result[0]: result[1] for result in result_tuples}
            return result_mapping
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_all_imeis(self):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sql = 'SELECT DISTINCT subscriber.imei FROM subscriber '
            sq_hlr_cursor.execute(sql)
            imeis = sq_hlr_cursor.fetchall()
            return imeis
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_matching_partial_imeis(self, partial_imei=''):
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sql = 'SELECT DISTINCT subscriber.imei FROM subscriber WHERE subscriber.imei LIKE ? ORDER BY subscriber.imei ASC'
            sq_hlr_cursor.execute(sql, [(partial_imei+'%')])
            imeis = sq_hlr_cursor.fetchall()
            return imeis
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_all_inactive_msisdns_since(self, days, ignore_prefix):
        """Get all msisdns that have been inactive for :days:, ignoring those
        beginning with the :ignore_prefix:
        """

        # TODO This function was migrated from existing code, and could
        #  probably use some refactoring.
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute(
                "SELECT msisdn FROM subscriber "
                "WHERE (length(msisdn) = 5 OR msisdn NOT LIKE ?) AND "
                "last_lu_seen < date('now', ?)",
                [(ignore_prefix+'%'), "-{} days".format(days)]
            )
            inactive = sq_hlr_cursor.fetchall()
            return inactive
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_all_inactive_roaming_msisdns(self, ignore_prefix):
        """Get all roaming msisdns (defined as length 11, unattached,
        from external prefix), ignoring those beginning with the
        :ignore_prefix:
        """

        # TODO This function was migrated from existing code, and could
        #  probably use some refactoring.
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute(
                "SELECT msisdn FROM subscriber "
                "WHERE length(msisdn) = 11 AND msisdn NOT LIKE ?",
                [(ignore_prefix+'%')]
            )

            inactive = sq_hlr_cursor.fetchall()
            return inactive
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def get_all_inactive_roaming_msisdns_since(self, days, ignore_prefix):
        """Get all roaming msisdns (defined as length 11, unattached,
        from external prefix) that have been inactive for :days:, ignoring
        those beginning with the :ignore_prefix:
        """

        # TODO This function was migrated from existing code, and could
        #  probably use some refactoring.
        sq_hlr = _open_sqlite_connection(self.hlr_db_path)
        try:
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute(
                "SELECT msisdn FROM subscriber "
                "WHERE length(msisdn) = 11 AND msisdn NOT LIKE ? AND "
                "last_lu_seen < date('now', ?)",
                [(ignore_prefix+'%'), "-{} days".format(days)]
            )

            inactive = sq_hlr_cursor.fetchall()
            return inactive
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        finally:
            sq_hlr.close()

    def show_by_msisdn(self, msisdn):
        vty = self._get_vty_connection()
        cmd = 'subscriber msisdn {} show'.format(msisdn)
        subscriber_data = vty.command(cmd, close=True)
        return subscriber_data

    def update_msisdn(self, current_msisdn, new_msisdn):
        vty = self._get_vty_connection()
        cmd = 'subscriber msisdn {} update msisdn {}'.format(
            current_msisdn, new_msisdn
        )
        vty.enabled_command(cmd, close=True)

    def delete_by_msisdn(self, msisdn):
        vty = self._get_vty_connection()
        cmd = 'subscriber msisdn {} delete'.format(msisdn)
        vty.enabled_command(cmd, close=True)

    def enable_access_by_msisdn(self, msisdn):
        self._set_access_by_msisdn(msisdn, "cs+ps")

    def disable_access_by_msisdn(self, msisdn):
        self._set_access_by_msisdn(msisdn, "none")

    def _set_access_by_msisdn(self, msisdn, access_string):
        vty = self._get_vty_connection()
        cmd = 'subscriber msisdn {} update network-access-mode {}'.format(
            msisdn, access_string
        )
        vty.enabled_command(cmd, close=True)

    def _get_vty_connection(self):
        if self._cached_vty is None:
            self._cached_vty = obscvty.VTYInteract(self._appstring, self._ip, self._vty_port)
        return self._cached_vty


def _open_sqlite_connection(path):
    try:
        return sqlite3.connect(path)
    except sqlite3.Error as e:
        raise OsmoHlrError("SQ_HLR connect error: {}".format(e))
