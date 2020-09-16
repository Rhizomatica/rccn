############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2013 tele <tele@rhizomatica.org>
# Copyright (C) 2016 keith <keith@rhizomatica.org>
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

""" Adaptor to interface with osmocom-nitb vty and db instead of hlr and msc
"""

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from config import NoDataException
from osmopy import obscvty
import logging
import sqlite3

log = logging.getLogger(__name__)


class OsmoHlrError(Exception):
    pass


class OsmoMscError(Exception):
    pass


class OsmoNitb(object):
    """Wraps NITB operations with an interface matching OsmoMsc and OsmoHlr

    The nitb db is not a stable interface, so updates may have to made to
    support changes to the db structure over time.

    The VTY itself is also not a stable interface, so changes and updates may
    need to happen here with new released versions of osmocom-nitb.
    """

    def __init__(self, ip_address, vty_port, hlr_db_path):
        self.hlr_db_path = hlr_db_path
        self._appstring = "OpenBSC"
        self._ip = ip_address
        self._vty_port = vty_port
        self._vty = obscvty

    def get_msisdn_from_imsi(self, imsi):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE imsi=%(imsi)s" % {'imsi': imsi})
            connected = sq_hlr_cursor.fetchone()
            sq_hlr.close()
            if len(connected) <= 0:
                raise OsmoHlrError('imsi %s not found' % imsi)
            return connected[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        except TypeError as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: number not found')

    def get_local_msisdn(self, imsi):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE imsi=%(imsi)s AND lac > 0" % {'imsi': imsi})
            connected = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if len(connected) <= 0:
                raise OsmoHlrError('imsi %s not found' % imsi)
            return connected[0]
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_imsi_from_msisdn(self, msisdn):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute('SELECT extension,imsi from subscriber WHERE extension=?', [(msisdn)])
            extension = sq_hlr_cursor.fetchone()
            if  extension == None:
                raise OsmoHlrError('Extension not found in the OsmoHLR')
            imsi = extension[1]
        except sqlite3.Error as e:
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])
        return str(imsi)

    def get_msisdn_from_imei(self, imei):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql = ('SELECT Equipment.imei, Subscriber.imsi, '
                   'Subscriber.extension, Subscriber.updated '
                   'FROM Equipment, EquipmentWatch, Subscriber '
                   'WHERE EquipmentWatch.equipment_id=Equipment.id '
                   'AND EquipmentWatch.subscriber_id=Subscriber.id '
                   'AND Equipment.imei=? '
                   'ORDER BY Subscriber.updated DESC LIMIT 1;')
            print(sql)
            sq_hlr_cursor.execute(sql, [(imei)])
            extensions = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return extensions
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_all_5digit_msisdns(self):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT id, extension FROM subscriber WHERE length(extension) = 5")
            extensions = sq_hlr_cursor.fetchall()
            if extensions == []:
                raise NoDataException('No extensions found')
            else:
                sq_hlr.close()
                return extensions
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_all_expire(self):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension,expire_lu FROM subscriber WHERE length(extension) = 11")
            subscribers = sq_hlr_cursor.fetchall()
            if subscribers == []:
                raise NoDataException('No subscribers found')
            else:
                sq_hlr.close()
                return subscribers
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_all_imeis(self):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql = 'SELECT DISTINCT Equipment.imei FROM Equipment '
            sq_hlr_cursor.execute(sql)
            imeis = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if imeis == []:
                return []
            if len(imeis) == 1:
                data = self.get_msisdn_from_imei(imeis[0][0])
                return data
            else:
                return imeis
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_matching_partial_imeis(self, partial_imei=''):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sql = 'SELECT DISTINCT Equipment.imei FROM Equipment '
            if partial_imei != '':
                sql += 'WHERE Equipment.imei LIKE ? ORDER BY Equipment.imei ASC'
                sq_hlr_cursor.execute(sql, [(partial_imei+'%')])
            else:
                sq_hlr_cursor.execute(sql)
            imeis = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            if imeis == []:
                return []
            if len(imeis) == 1:
                data = self.get_msisdn_from_imei(imeis[0][0])
                return data
            else:
                return imeis
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_msisdns_since(self, days, ignore_prefix):
        """Get all msisdns that have been inactive for :days:, ignoring those
        beginning with the :ignore_prefix:
        """
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE (length(extension) = 5 OR extension NOT LIKE \"%(prefix)s%%\") AND updated < date('now', '-%(days)s days')" % {'days': days, 'prefix': ignore_prefix})
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive

        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_roaming_msisdns(self, ignore_prefix):
        """Get all roaming msisdns (defined as length 11, unattached,
        from external prefix) , ignoring those beginning with the
        :ignore_prefix:
        """
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT extension FROM subscriber WHERE length(extension) = 11 AND extension NOT LIKE '%s%%' AND lac = 0" % ignore_prefix)
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def get_all_inactive_roaming_msisdns_since(self, days, ignore_prefix):
        """Get all roaming msisdns (defined as length 11, unattached,
        from external prefix) that have been inactive for :days:, ignoring
        those beginning with the :ignore_prefix:
        """
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            _sql=("SELECT extension FROM subscriber WHERE length(extension) = 11 AND extension NOT LIKE \"%(prefix)s%%\" AND lac = 0 AND updated < date('now', '-%(days)s days')" % {'days': days, 'prefix': ignore_prefix})
            sq_hlr_cursor.execute(_sql)
            inactive = sq_hlr_cursor.fetchall()
            sq_hlr.close()
            return inactive
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoHlrError('SQ_HLR error: %s' % e.args[0])

    def show_by_msisdn(self, msisdn):
        vty = self._vty.VTYInteract(self._appstring, self._ip, self._vty_port)
        cmd = 'show subscriber extension {}'.format(msisdn)
        subscriber_data = vty.command(cmd, close=True)
        return subscriber_data

    def update_msisdn(self, current_msisdn, new_msisdn):
        vty = self._vty.VTYInteract(self._appstring, self._ip, self._vty_port)
        cmd = 'subscriber extension {} extension {}'.format(
            current_msisdn, new_msisdn
        )
        vty.enabled_command(cmd, close=True)

    def delete_by_msisdn(self, msisdn):
        vty = self._vty.VTYInteract(self._appstring, self._ip, self._vty_port)
        cmd = 'subscriber extension {} delete'.format(msisdn)
        vty.enabled_command(cmd, close=True)

    def enable_access_by_msisdn(self, msisdn):
        vty = self._vty.VTYInteract(self._appstring, self._ip, self._vty_port)
        cmd = 'subscriber extension {} authorized 1'.format(msisdn)
        vty.enabled_command(cmd, close=True)

    def disable_access_by_msisdn(self, msisdn):
        vty = self._vty.VTYInteract(self._appstring, self._ip, self._vty_port)
        cmd = 'subscriber extension {} authorized 0'.format(msisdn)
        vty.enabled_command(cmd, close=True)

    def get_active_subscribers(self):
        try:
            sq_hlr = sqlite3.connect(self.hlr_db_path)
            sq_hlr_cursor = sq_hlr.cursor()
            sq_hlr_cursor.execute("SELECT imsi, extension FROM subscriber WHERE lac > 0")
            connected = sq_hlr_cursor.fetchall()
            sq_hlr.close()
        except sqlite3.Error as e:
            sq_hlr.close()
            raise OsmoMscError('SQ_HLR error: %s' % e.args[0])

        subscriber_list = []
        for (imsi, msisdn) in connected:
            subscriber_list.append({"imsi": imsi, "msisdn": msisdn})

        return subscriber_list

    def expire_subscriber_by_msisdn(self, msisdn):
        try:
            vty = obscvty.VTYInteract(self._appstring, self._ip, self._vty_port)
            cmd = "subscriber extension {} expire".format(msisdn)
            return_text = vty.enabled_command(cmd, close=True)
            if return_text:
                raise OsmoMscError("VTY cmd: `{}` returned: `{}`".format(cmd, return_text))
        except IOError:
            log.debug('Exception in expire_lu!', exc_info=True)


def _open_sqlite_connection(path):
    try:
        return sqlite3.connect(path)
    except sqlite3.Error as e:
        raise OsmoHlrError("SQ_HLR connect error: {}".format(e))


if __name__ == "__main__":
    print(OsmoNitb("127.0.0.1", 4242, "/var/lib/osmocom/hlr.db").show_by_msisdn(36851))
