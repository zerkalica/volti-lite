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

import os
from ConfigParser import RawConfigParser, DEFAULTSECT
from mixerbase import CardInfo
from debug import log

class ConfigAbstract(RawConfigParser):
    _defaults = {}
    app_name = ""
    app_version = ""
    def __init__(self, filename = "config"):
        """ Constructor """
        RawConfigParser.__init__(self, self._defaults)
        self.res_dir = None
        self.locale_dir = None
        self.updated = False
        self.set_filename(filename)
        self.load()

    def set_filename(self, filename):
        if not os.path.isdir(os.path.join(".","src")):
            for base in ["/usr/share", "/usr/local/share"]:
                if os.path.isdir(os.path.join(base, self.app_name)):
                    self.res_dir = os.path.join(base, self.app_name)
                    self.locale_dir = os.path.join(base, "locale")
                    break

        if not self.res_dir:
            self.res_dir = "data"

        self.config_dir = os.path.expanduser(os.path.join("~", ".config", self.app_name))
        self.config_file = os.path.join(self.config_dir, filename)
        
    def get_default_section(self):
        return DEFAULTSECT
        
    def readfile(self):
        return self.read(self.config_file)
    
    def get(self, section, option):
        #@bug in ConfigParser.RawConfigParser.getboolean, which work only with string
        return str(RawConfigParser.get(self, section, option))
    
    def set(self, section, option, value):
        self.updated = True
        log.Notice("set value %s for option %s" %(value, option), 1)
        RawConfigParser.set(self, section, option, value)
    
    def save(self):
        """ Write config file """
        if (not self.updated):
            return
            
        if not os.path.isdir(self.config_dir):
            try:
                os.makedirs(self.config_dir)
            except OSError:
                pass
        log.Notice("Saving config to %s" % self.config_file)
        configfile = open(self.config_file, 'w')
        self.write(configfile)
        self.updated = False

    def load(self):
        return self.readfile()
    
class Config(ConfigAbstract):

    _defaults = {
    "card_index": 0,
    "mixer": "alsamixer",
    "run_in_terminal": "true",
    "mixer_internal": "true",
    "mixer_show_values": "true",
    "scale_increment": 5.0,
    "scale_show_value": "true",
    "show_tooltip": "true",
    "toggle": "mute",
    "show_notify": "true",
    "notify_timeout": 3.0,
    "notify_position": "true",
    "notify_body": '<span font_desc="14" weight="bold">{volume}</span>\n<small>{card}</small>\n<small>{mixer}</small>'
    }
    app_name = "voltilite"
    app_version = "0.1-svn"

    def __init__(self, filename = "config"):
        """ Constructor """
        ConfigAbstract.__init__(self, filename)

    def get_card_section(self):
        return self.get_card_section_name(self.getint(self.get_default_section(), "card_index"))

    def get_card_section_name(self, card_index):
        return "card-%s" % card_index
    
    def set_card_index(self, card_index):
        log.Notice("set card_index = %s" % card_index)
        self.set(self.get_default_section(), "card_index", card_index)
        self.check_card_index(card_index)
    
    def check_card_index(self, card_index):
        section = self.get_card_section()
        if ( not self.has_section(section) ):
            self.add_section(section)
        if ( not self.has_option(section, "control") ):
            self.set_card_mixer()
            
    def set_card_mixer(self, mixer = None, cid = 0):
        if( not mixer ):
            mixers = CardInfo.get_mixers(self.getint(self.get_default_section(), "card_index"))
            if (mixers):
                (mixer, cid) = mixers[0]
            else:
                mixer = "Master"
        c = self.get_card_section()
        self.set(c, "control", mixer)
        self.set(c, "cid", cid)
        
    def load(self):
        readed = ConfigAbstract.readfile(self)
        if ( not readed or not self.has_section(self.get_card_section()) ):
            card_index = self.getint(self.get_default_section(), "card_index")
            self.set_card_index(card_index)
        if not readed:
            self.updated = True
            self.save()
