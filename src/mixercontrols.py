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

import gtk
import os
from abc import abstractmethod
from mixerbase import MixerControlLocableAbstract
from debug import log

class VolumeSlider(gtk.VScale):
    def __init__(self, show_value, channel_index, max, default, hook):
        self.channel_index = channel_index
        self.adjustment = gtk.Adjustment(0.0, 0.0, 100.0, 1.0, 10.0, 0.0)
        gtk.VScale.__init__(self, self.adjustment)
        self.set_inverted(True)
        self.set_draw_value(show_value)
        self.set_digits(0)
        self.set_size_request(-1, 250)
        self.set_value_pos(gtk.POS_TOP)
        gtk.VScale.set_value(self, default)
        self.connect_handler = gtk.VScale.connect(self, "value_changed", hook)
        
    def set_value(self, value):
        self.handler_block(self.connect_handler)
        gtk.VScale.set_value(self, value)
        self.handler_unblock(self.connect_handler)

    def get_value_converted(self):
        return int(gtk.VScale.get_value(self))
    
class ToggleButtonAbstract(gtk.ToggleButton):
    def __init__(self, res_dir, active=False, hook=None):
        gtk.ToggleButton.__init__(self)
        self.hook = hook
        self.res_dir = res_dir
        image = self.get_image(active)
        self.set_property("image", image)
        self.connect_handler = self.connect("toggled", self.on_toggle)
        self.set_active(int(active))
    
    def set_active(self, value):
        self.handler_block(self.connect_handler)
        gtk.ToggleButton.set_active(self, value)
        self.handler_unblock(self.connect_handler)
    
    def on_toggle(self, button):
        active = bool(button.get_active())
        image = self.get_image(active)
        button.set_property("image", image)
        if (self.hook):
            self.hook(active)
        return active

    @abstractmethod
    def get_active_icon(self):
        pass

    @abstractmethod
    def get_normal_icon(self):
        pass
                
    def get_image(self, active):
        if (active):
            icon = self.get_active_icon()
        else:
            icon = self.get_normal_icon()
        image = gtk.Image()
        image.set_from_file(os.path.join(self.res_dir, "icons", icon))
        image.show()
        return image

class RecButton(ToggleButtonAbstract):
    def get_active_icon(self):
        return "mixer-record.png"        
    def get_normal_icon(self):
        return "mixer-no-record.png"        

class MuteButton(ToggleButtonAbstract):
    def get_active_icon(self):
        return "mixer-muted.png"        
    def get_normal_icon(self):
        return "mixer-no-muted.png"        

class LockButton(ToggleButtonAbstract):
    def get_active_icon(self):
        return "mixer-lock.png"        
    def get_normal_icon(self):
        return "mixer-no-lock.png"        
      
class MixerControl(MixerControlLocableAbstract):
    """
    A Class that implements a volume control (stereo or mono) for a sound card
    mixer. Each instance represents one mixer channel on the sound card.
    """

    def __init__(self, config, card_index, control, cid):
        MixerControlLocableAbstract.__init__(self, config, card_index, control, cid)
        self.sliders = []
        self.buttons = {}
        
    def __del__(self):
        MixerControlLocableAbstract.__del__(self)
        
    def _make_control(self):
        self.sliders = []
        self.buttons = {}
        max = self.get_channel_count()
        show_value = self.config.getboolean(self.config.get_default_section(), "mixer_show_values")
        
        volumes = self.get_volume()
        for channel_index, volume in enumerate(volumes):
            self.sliders.append( VolumeSlider(show_value, channel_index, max, volume, self.on_slider_value_changed) )
        
        self.buttons['mute'] = MuteButton(self.config.res_dir, self.get_mute(), self.on_mute_button)
        
        rec = self.get_rec()
        if ( rec != None):
            self.buttons['rec'] = RecButton(self.config.res_dir, rec, self.on_rec_button)
        if (self.get_channel_count() > 1):
            self.buttons['lock'] = LockButton(self.config.res_dir, self.get_lock(), self.on_lock_button)
            
        control_box = gtk.HBox(True, 0)
        for slider in self.sliders:
            control_box.pack_start(slider, True, True)
            
        option_box = gtk.HBox(True, 0)
        for type, button in self.buttons.iteritems():
            option_box.pack_start(button, False, False)
        
        vbox = gtk.VBox()
        
        vbox.pack_start(control_box, True, True)
        vbox.pack_start(option_box, False, False, 5)
        
        align = gtk.Alignment(xscale=1, yscale=1)
        align.set_padding(5, 5, 5, 5)
        align.add(vbox)
        return align
        
    
    def on_rec_button(self, active):
        log.Notice("rec button state changed to %s" % active)
        self.set_rec(active)

    def on_lock_button(self, active):
        self.set_lock(active)
        log.Notice("lock button state changed to %s = %s" % (active, self.get_lock()))
    
    def on_mute_button(self, active):
        log.Notice("mute button state changed to %s" % active)
        self.set_mute(bool(active))
            
    def on_slider_value_changed(self, slider, data=None):
        volume = int(slider.get_value())
        if(self.get_lock()):
            self._slider_sync_values(slider, volume)
        self.set_volume(volume, slider.channel_index)
        
        
    def _slider_sync_values(self, slider, volume):
        """if locked, set all other sliders to same value"""
        for current_slider in self.sliders:
            if (current_slider.channel_index != slider.channel_index):
                current_slider.set_value(volume)
                self.set_volume(volume, current_slider.channel_index)
                
    def on_volume_changed(self, volume):
        log.Notice("volume changed by other side to %s" % volume)
        event_from_external_source = True
        if (event_from_external_source):
            for slider in self.sliders:
                slider.set_value(volume[slider.channel_index])
            
        
    def on_mute_changed(self, mute):
        log.Notice("mute state changed by other side to %s" % mute)
        event_from_external_source = True
        if (event_from_external_source):
            self.buttons['mute'].set_active( mute )
    
    def on_any_changed(self, volume, mute):
        pass
        
class MixerControlFrame(MixerControl):
    def __init__(self, config, card_index, control, cid):
        MixerControl.__init__(self, config, card_index, control, cid)
        
        label = self.get_label(control, cid)
        self.frame = gtk.Frame(label)
        self.frame.set_label_align(0.5, 0.8)
        
        self.align = self._make_control()
        self.frame.add( self.align )
        
    def __del__(self):
        MixerControl.__del__(self)
        self.frame.destroy()
        
    def update(self, card_index, control, cid):
        self.frame.remove( self.align )
        MixerControl.update(self, card_index, control, cid)
        self.align = self._make_control()
        self.frame.add( self.align )
        label = self.get_label(control, cid)
        self.frame.set_label(label)
        
    def get_label(self, control, cid):
        if (cid != 0):
            label = "%s %i" % (control, cid)
        else:
            label = control
        return label
        

class ApplicationAbstract:
    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass
        
    @staticmethod
    def quit(widget=None):
        """ Quit main loop """
        gtk.main_quit()
