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

import sys
import gettext
import gtk
import os
from config import Config
from debug import log
from icons import Icons
from mixercontrols import MixerControlFrame, ApplicationAbstract
from mixerbase import MixerHandler
from mixerhelper import MixerHelper
from preferences import Preferences
from notification import Notification

class TrayMixerControlFrame(MixerControlFrame):
    def __init__(self, config, on_volume_changed_hook, on_mute_changed_hook):
        self.mixer_handle = False
        self.config = config
        
        self.on_volume_changed_hook = on_volume_changed_hook
        self.on_mute_changed_hook = on_mute_changed_hook
        
        [card_index, control_name, cid] = self.get_config_params()
        MixerControlFrame.__init__(self, config, card_index, control_name, cid)
        self.mixer_handle = MixerHandler.connect(self.on_change)
        self.frame.set_shadow_type(gtk.SHADOW_OUT)

    def update(self):
        [card_index, control_name, cid] = self.get_config_params()
        MixerHandler.disconnect(self.mixer_handle)
        MixerControlFrame.update(self, card_index, control_name, cid)
        self.frame.set_shadow_type(gtk.SHADOW_OUT)
        self.mixer_handle = MixerHandler.connect(self.on_change)
        
    def get_config_params(self):
        card_index = self.config.getint(self.config.get_default_section(), "card_index")
        control_name = self.config.get(self.config.get_card_section_name(card_index), "control")
        cid = self.config.getint(self.config.get_card_section_name(card_index), "cid")
        return [card_index, control_name, cid]
        
    def __del__(self):
        MixerHandler.disconnect(self.mixer_handle)
        MixerControlFrame.__del__(self)
        
    def on_volume_changed(self, volume):
        MixerControlFrame.on_volume_changed(self, volume)
        self.on_volume_changed_hook(True)
        
    def on_mute_button(self, active):
        MixerControlFrame.on_mute_button(self, active)
        self.on_mute_changed_hook(False)
        
    def on_mute_changed(self, mute):
        MixerControlFrame.on_mute_changed(self, mute)
        self.on_mute_changed_hook(True)
        
    def on_slider_value_changed(self, slider, data=None):
        MixerControlFrame.on_slider_value_changed(self, slider, data)
        self.on_volume_changed_hook(False)
    
    def toggle_mute(self):
        self.on_mute_button(not self.get_mute())
        
    def inc_volume(self):
        self._step_change_volume(False)
    
    def dec_volume(self):
        self._step_change_volume(True)
        
    def _step_change_volume(self, step_down):
        inc = self.config.getfloat(self.config.get_default_section(), "scale_increment")
        volume = self.get_volume()
        volume = float(volume[0])
        if (step_down):
            volume = max(0, volume - inc)
        else:
            volume = min(100, volume + inc)
        volume = int(volume)
        volume = [volume] * self.get_channel_count()
        self.set_volume(volume[0])
        
        MixerControlFrame.on_volume_changed(self, volume)
        self.on_volume_changed_hook(False)
        
        #self.on_volume_changed(volume)
        

class TrayMixerWindow(gtk.Window): 
    def __init__(self, config, on_volume_changed_hook, on_mute_changed_hook, get_geometry_hook):
        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)
        
        self.get_geometry_hook = get_geometry_hook
        
        self.mixer = TrayMixerControlFrame(config, on_volume_changed_hook, on_mute_changed_hook)
        
        self.resize(1, 1)
        self.add(self.mixer.frame)
        self.connect_after("realize", self.on_realize)
        self.connect("key_release_event", self.on_window_key_release_event)
        self.connect("button_press_event", self.on_window_button_press_event)

    def update(self):
        self.release_grab()
        self.hide()
        self.remove(self.mixer.frame)
        self.mixer.update()
        self.add(self.mixer.frame)
    
    def __del__(self):
        del self.mixer
    
    def on_realize(self, widget):
        """ Callback for realize. Move window when realized """
        self.move_window()
        
    def move_window(self):
        """ Move scale window """
        posx, posy = self.get_position()
        self.move(posx, posy)
        
    def get_position(self):
        """ Get coordinates to place scale window """
        screen, rectangle, orientation = self.get_geometry_hook()
        self.set_screen(screen)
        window = self.allocation
        monitor_num = screen.get_monitor_at_point(rectangle.x, rectangle.y)
        monitor = screen.get_monitor_geometry(monitor_num)

        if orientation == gtk.ORIENTATION_VERTICAL:
            if monitor.width - rectangle.x == rectangle.width:
                # right panel
                posx = monitor.x + monitor.width - window.width - rectangle.width
            else:
                # left panel
                posx = rectangle.x + rectangle.width
            posy = rectangle.y
        else:
            if (rectangle.y + rectangle.height + window.height <= monitor.y + monitor.height):
                posy = rectangle.y + rectangle.height
            else:
                posy = rectangle.y - window.height

            if (rectangle.x + window.width <= monitor.x + monitor.width):
                posx = rectangle.x
            else:
                posx = monitor.x + monitor.width - window.width

        return posx, posy
    
    def toggle(self):
        visible = self.get_property("visible")
        if (visible):
            self.release_grab()
        else:
            self.grab_window()
            
    def grab_window(self):
        """ Grab and focus window """
        self.show_all()
        
        gtk.gdk.pointer_grab(self.window, True,
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK | 
            gtk.gdk.POINTER_MOTION_MASK | 
            gtk.gdk.SCROLL_MASK)

        if gtk.gdk.pointer_is_grabbed():
            gtk.gdk.keyboard_grab(self.window, True)
        return True
    
    def release_grab(self):
        """ Release grab from window """
        display = self.get_display()
        display.keyboard_ungrab()
        display.pointer_ungrab()
        self.grab_remove()
        self.hide()
    
    def on_window_key_release_event(self, widget, event):
        """ Callback for key_release_event. On non-navigation keys release window """
        grab_keys = (65364, 65362, 65366, 65365, 65361, 65367, 65360)
        if not event.keyval in (grab_keys):
            self.release_grab()
        return True

    def on_window_button_press_event(self, widget, event):
        """ Callback for button_press_event. If clicked somewhere else release window """
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.release_grab()
            return True
        return False

class TrayIcon(gtk.StatusIcon):
    """ GTK+ application for controlling audio volume from system tray/notification area """
    def __init__(self, config):
        gtk.StatusIcon.__init__(self)
        self.config = config

    def update(self, info):
        """ Update icon """
        [volume, muted, var, card_name, mixer_name] = info
        vol = volume[0]
        if (muted):
            vol = 0
        icon = Icons.get_icon_name_by_volume(vol)
        self.set_from_icon_name(icon)
        
        #""" Update tooltip """
        tooltip = "<b>%s: %s%s </b>\n<small>%s: %s\n%s: %s</small>" % (
                _("Output"), Icons.get_volume_name(vol, muted),
                var, _("Card"), card_name,
                _("Mixer"), mixer_name)
        self.set_tooltip_markup(tooltip)
            
class TrayPopupMenu(gtk.Menu):
    """ Popup menu """
    def __init__(self, config, on_mute_button_hook, get_mute_hook, on_quit_hook, on_show_preferences_hook, parent):
        self.config = config
        gtk.Menu.__init__(self)
        self.parent_widget = parent
        self.on_mute_button_hook = on_mute_button_hook
        self.get_mute_hook = get_mute_hook

        self.item_mute = gtk.CheckMenuItem(_("Mute"))
        self.mute_handler_id = self.item_mute.connect("toggled", self.on_toggle_mute)
        self.add(self.item_mute)

        item = gtk.ImageMenuItem(_("Show Mixer"))
        item.connect("activate", self.on_show_mixer)
        self.add(item)

        item = gtk.ImageMenuItem("gtk-preferences")
        item.connect("activate", on_show_preferences_hook)
        self.add(item)

        item = gtk.ImageMenuItem("gtk-quit")
        item.connect("activate", on_quit_hook)
        self.add(item)
        
        self.update_items()
        self.show_all()
        
    def update_items(self):
        self.item_mute.handler_block(self.mute_handler_id)
        self.item_mute.set_active(self.get_mute_hook())
        self.item_mute.handler_unblock(self.mute_handler_id)
        
    def on_popup_event(self, status, button, time):
        self.update_items()
        self.popup(None, None, gtk.status_icon_position_menu, button, time, self.parent_widget)

    def on_toggle_mute(self, widget=None):
        """ Toggles mute status """
        self.on_mute_button_hook(widget.get_active())

    def on_show_mixer(self, widget=None, data=None):
        """ Start mixer app in new thread """
        mixer_starter = MixerHelper(self.config)
        mixer_starter.run()
        
class TrayApplication(ApplicationAbstract):
    
    def __init__(self):
        self.config = Config()
        self.preferences = False
        self.control = False
    
        gettext.bindtextdomain(self.config.app_name, self.config.locale_dir)
        gettext.textdomain(self.config.app_name)
        import __builtin__
        __builtin__._ = gettext.gettext
        
        self.tray = TrayIcon(self.config)
        
        self.control = TrayMixerWindow(self.config,
                                       self.on_volume_changed,
                                       self.on_mute_changed,
                                       self.tray.get_geometry)
        
        self.menu = TrayPopupMenu(self.config,
                                  self.control.mixer.on_mute_button,
                                  self.control.mixer.get_mute,
                                  self.quit,
                                  self.on_show_preferences,
                                  self.tray
                                  )
        
        self.tray.connect("popup_menu", self.menu.on_popup_event)
        self.tray.connect("button_press_event", self.on_tray_press_event)
        self.tray.connect("scroll_event", self.on_window_scroll_event)
        
        self.notify = False
        self.update_notify()
        self.update()
        
    def update_notify(self):
        show = self.config.getboolean(self.config.get_default_section(), "show_notify")
        if (self.notify):
            if (show):
                del self.notify
                self.notify = False
            else:
                self.notify.reopen()
        else:
            if (show):
                self.notify = Notification(self.config, self.tray.get_geometry)
            else:
                self.notify = False
        
        
    def update(self):
        info = self.control.mixer.get_status_info()
        self.tray.update(info)
        if (self.notify):
            self.notify.update(info)
    
    def show(self):
        log.Notice("update_show", 1)
        if (self.notify):
            self.notify.show()
    
    def on_volume_changed(self, show):
        self.update()
        if (show):
            self.show()

    def on_mute_changed(self, show):
        self.on_volume_changed(show)
        
    def on_tray_press_event(self, widget, event, data=None):
        if event.button == 1:
            self.control.toggle()
        elif event.button == 2:
            toggle = self.config.get(self.config.get_default_section(), "toggle")
            if (toggle == "mute"):
                self.control.mixer.toggle_mute()
                self.update()
            elif (toggle == "mixer"):
                self.menu.on_show_mixer()
                
    def on_window_scroll_event(self, widget, event):
        log.Notice("scroll event")
        if event.direction == gtk.gdk.SCROLL_UP:
            self.control.mixer.inc_volume()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.control.mixer.dec_volume()

    def on_show_preferences(self, widget=None, data=None):
        """ Show preferences window """
        self.preferences = Preferences(self.config, self.on_preferences_close, self.on_preferences_update)
        
    def on_preferences_update(self):
        log.Notice("preferences update")
        self.control.update()
        self.update_notify()
        self.update()
        
    def on_preferences_close(self):
        self.config.save()
        
    
