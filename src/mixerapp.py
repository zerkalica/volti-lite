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
from config import Config
from debug import log
from mixercontrols import MixerControlFrame, ApplicationAbstract
from mixerbase import MixerAbstract, CardInfo, MixerHandler

class Mixer(MixerAbstract):
    def __init__(self, config, card_index, card_name):
        self.card_name = card_name
        self.hbox = gtk.HBox(False, 10)
        align = gtk.Alignment(xscale=1, yscale=1)
        align.set_padding(10, 10, 10, 10)
        align.add(self.hbox)
        
        vbox = gtk.VBox()
        vbox.add(align)
        
        self.frame = gtk.Frame()
        self.frame.add(vbox)

        MixerAbstract.__init__(self, config, card_index)
        
    def __del__(self):
        MixerAbstract.__del__(self)

    def add_control(self, control):
        self.hbox.pack_start(control.frame, True, True)
        MixerAbstract.add_control(self, control)    
        
    def del_control(self, control):
        self.hbox.pack_end(control.frame)
        MixerAbstract.del_control(self, control)
        
    def init(self):
        for control_name, cid in CardInfo.get_mixers(self.card_index):
            self.add_control(MixerControlFrame(self.config, self.card_index, control_name, cid))
            

class MixersContainer(gtk.Notebook):
    def __init__(self, config):
        gtk.Notebook.__init__(self)
        self.config = config
        self.mixers = []
        self.set_tab_pos(gtk.POS_TOP)
        self.mixer_handle = MixerHandler.connect(self.on_change)
        
    def __del__(self):
        MixerHandler.disconnect(self.mixer_handle)
        
        for mixer in self.mixers:
            for control in mixer.controls:
                if ( control.control == "PCM"):
                    log.Notice("%s=%s" % (control.control, control.get_lock()))
        
        for mixer in self.mixers:
            #self.remove_page(mixer.frame)
            del mixer
            
    def set_default_page(self):
        default_card_index = self.config.getint(self.config.get_default_section(), "card_index")
        log.Notice("set default page %s" % default_card_index)
        self.set_current_page(default_card_index)
        
    def add_mixer(self, mixer):
        self.append_page(mixer.frame, gtk.Label(mixer.card_name))
        self.mixers.append(mixer)
        
    def del_mixer(self, mixer):
        self.remove_page(mixer.frame)
        self.mixers.remove(mixer)
        del mixer

    def init(self):
        for card_index, card_name in enumerate(CardInfo.get_cards()):
            self.add_mixer(Mixer(self.config, card_index, card_name))

    def save(self):
        for mixer in self.mixers:
            mixer.save()

    def load(self):
        for mixer in self.mixers:
            mixer.load()

    def on_change(self, source=None, condition=None):
        #gtk.gdk.threads_enter()
        for mixer in self.mixers:
            mixer.on_change()
        return True
        #gtk.gdk.threads_leave()
    
class MixersWindow(gtk.Window):
    """ Volti Mixer Application"""

    def __init__(self, config):
        gtk.Window.__init__(self)
        self.set_title("Volti Mixer")
        self.set_resizable(True)
        self._set_icon_name_file()
        self.mixerscontainer = MixersContainer(config)
        self.add(self.mixerscontainer)
        self.mixerscontainer.init()
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('delete_event', self.quit)
        self.show_all()
        self.mixerscontainer.set_default_page()

    def __del__(self):
        log.Notice("deleting main window")
        del self.mixerscontainer

    def _set_icon_name_file(self, name="multimedia-volume-control"):
        icon_theme = gtk.icon_theme_get_default()
        if icon_theme.has_icon(name):
            self.set_icon_name(name)
        else:
            file = os.path.join(
                    self.config.res_dir, "icons", name + ".svg")
            self.set_icon_from_file(file)

    def save(self):
        self.mixerscontainer.save()

    def quit(self, element=None, event=None):
        """ Exit main loop """
        log.Notice("exiting")
        self.save()
        ApplicationAbstract.quit(self)

class MixersApplication(ApplicationAbstract):
    def __init__(self):
        self.config = Config()
        self.mixer = MixersWindow(self.config)

    def __del__(self):
        log.Notice("deleting app window")
        self.config.save()
        del self.config
        del self.mixer
