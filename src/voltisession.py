# -*- coding: utf-8 -*-

# Author: Milan Nikolic <gen2brain@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from dbus import SessionBus, bus
from dbus.mainloop.glib import DBusGMainLoop
from debug import log

class VoltiSession:
    def __init__(self, app_name):
        log.Notice("running init")
        self.app_name = app_name
        self.bus = SessionBus(mainloop = DBusGMainLoop() )

    def check(self):
        log.Notice("running check")
        return self.bus.request_name(self.app_name) != bus.REQUEST_NAME_REPLY_PRIMARY_OWNER
