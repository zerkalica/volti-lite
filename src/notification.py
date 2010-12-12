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

import dbus
from debug import log
from icons import Icons

class Notification:
    """ Desktop notifications """

    def __init__(self, config, get_geometry_hook):
        """ Constructor """
        self.config = config
        self.last_id = None
        self.info = False
        self.get_geometry_hook = get_geometry_hook
        self.open()
        
    def open(self):
        bus = dbus.SessionBus()
        obj = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        self.notify = dbus.Interface(obj, 'org.freedesktop.Notifications')
        self.server_capable = self.check_capabilities()
        if (self.server_capable):
            self.title = _("Mixer")
        else:
            self.title = ""
        self.last_id = dbus.UInt32()

    def close(self):
        """ Close the notification """
        if self.last_id:
            self.notify.CloseNotification(self.last_id)
            self.last_id = None
            
    def reopen(self):
        self.close()
        self.open()
            
    def update(self, info):
        """ Update notification """
        self.info = info
    
    def __del__(self):
        log.Notice("destroy", 1)
        self.close()

    def check_capabilities(self):
        info = self.notify.GetServerInformation()
        log.Notice("notify %s" % str(info[0]))
        return bool(info[0] != "notify-osd")

    def show(self):
        """ Show the notification """
        if (not self.info):
            return
        
        duration = self.config.getfloat(self.config.get_default_section(), "notify_timeout")
        
        [volume, muted, var, card_name, mixer_name] = self.info
        volume = volume[0]
        icon = Icons.get_icon_name_by_volume(volume)
        
        body = self.format(volume, muted, var, card_name, mixer_name)
        hints = {"urgency": dbus.Byte(0), "desktop-entry": dbus.String("volti")}
        
        if self.config.getboolean(self.config.get_default_section(), "notify_position") and self.server_capable:
            hints["x"], hints["y"] = self.get_position()
            
        self.last_id = self.notify.Notify('volume', self.last_id, icon, self.title, body, [], hints, duration * 1000)

    def get_position(self):
        """ Returns status icon center coordinates """
        screen, rectangle, orientation = self.get_geometry_hook()
        posx = rectangle.x + rectangle.width/2
        posy = rectangle.y + rectangle.height/2
        return posx, posy

    def format(self, volume, muted, var, card_name, mixer_name):
        """ Format notification body """
        message = self.config.get(self.config.get_default_section(), "notify_body")
        volume = Icons.get_volume_name(volume, muted)
        message = message.replace('{volume}', '%s%s' % (volume, var))
        message = message.replace('{card}', '%s: %s' % (_("Card"), card_name))
        message = message.replace('{mixer}', '%s: %s' % (_("Mixer"), mixer_name))
        return message
