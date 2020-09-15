############################################################################
#
# RCCN (Rhizomatica Community Cellular Network)
#
# Copyright (C) 2020 matt9j <matt9j@cs.washington.edu>
#
# Loosely based on GPL-3 example code from
# http://git.osmocom.org/python/osmo-python-tests/tree/scripts/osmo_ctrl.py
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

""" This module contains adaptors to interface with osmo-msc

Interfaces are provided via the osmo-ctrl interface, which is supposed to be
a relatively stable API.
"""

# Python3/2 compatibility
# TODO: Remove once python2 support no longer needed.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import socket
from osmopy.osmo_ipa import Ctrl
from osmopy import obscvty


class OsmoMscError(Exception):
    pass


class OsmoMsc(object):
    """Encapsulates communication with an external MSC

    This class is synchronous and calls to methods may block for network
    communication.
    """
    def __init__(self, ip_address, ctrl_port, vty_port):
        self._ip_address = ip_address
        self._ctrl_port = ctrl_port
        self._vty_port = vty_port
        self._vty_appstring = "OsmoMSC"

    def get_active_subscribers(self):
        try:
            with SynchronousCtrlConnection(self._ip_address, self._ctrl_port) as conn:
                subscribers = conn.get_value("subscriber-list-active-v1")
        except (CtrlNoResponseError, socket.timeout, OSError) as e:
            raise OsmoMscError("Ctrl Interface failure {}", str(e))

        # Drop the leading key name and trailing whitespace
        subscribers = subscribers.split(" ")[1].strip()

        subscriber_list = []

        if len(subscribers) > 0:
            # Split on newlines for the payload
            for subscriber in subscribers.split("\n"):
                (imsi, msisdn) = subscriber.split(",")
                subscriber_list.append({"imsi": imsi, "msisdn": msisdn})

        return subscriber_list

    def expire_subscriber_by_msisdn(self, msisdn):
        try:
            vty = obscvty.VTYInteract(self._vty_appstring, self._ip_address, self._vty_port)
            cmd = "subscriber extension {} expire".format(msisdn)
            return_text = vty.enabled_command(cmd, close=True)
            if return_text:
                raise OsmoMscError("VTY cmd: `{}` returned: `{}`".format(cmd, return_text))
        except IOError:
            # TODO(matt9j) Log that communication failed with the MSC.
            pass


class CtrlNoResponseError(RuntimeError):
    pass


class SynchronousCtrlConnection(object):
    """A simple osmo-ctrl connection receiver

    This class is not multithread safe, and is not save to use with traps
    enabled since its socket message parsing is very simplistic and could be
    thrown off by partial messages received concurrently over stream socket.
    """
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._ctrl = Ctrl()

    def __enter__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setblocking(True)
        self._sock.settimeout(5.0)  # Timeout in seconds
        self._sock.connect((self._host, self._port))
        return self

    def __exit__(self, type, value, traceback):
        self._sock.close()

    def get_value(self, key):
        (msg_id, payload) = self._ctrl.cmd(key, val=None)
        self._sock.send(payload)

        while True:
            return_payload = self._sock.recv(8192)
            return self._parse_for_id(return_payload, msg_id)

    def _parse_for_id(self, payload, sought_id):
        while len(payload) > 0:
            (message_bytes, payload_remaining) = self._ctrl.split_combined(payload)
            (msg_id, message, _) = self._ctrl.parse(message_bytes)
            msg_id = int(msg_id)
            if msg_id == sought_id:
                return message
            payload = payload_remaining

        raise CtrlNoResponseError("No response with id {} found".format(sought_id))


if __name__ == "__main__":
    uut = OsmoMsc("127.0.0.1", 4255)
    print(uut.get_active_subscribers())
