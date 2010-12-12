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
from utils import utils
from subprocess import Popen, PIPE
from debug import log
from threading import Thread

class MixerHelper():
    """ Volti Mixer Helper"""
    def __init__(self, config):
        self.config = config
        
    def run(self):
        return Thread( target = self.toggle_mixer() ).start()
        
    def toggle_mixer(self):
        """ Toggle mixer application """
        mixer = self.get_mixer_name()
        run = self.config.getboolean(self.config.get_default_section(), "run_in_terminal") and not self.config.getboolean(self.config.get_default_section(), "mixer_internal")
        log.Notice("Launching mixer %s / %s" % (mixer, run) )
        if not mixer:
            return
        try:
            pid = self._mixer_get_pid()
            if pid:
                os.kill(pid, SIGTERM)
            else:
                if (run):
                    term = utils.find_term()
                    cmd = [term, "-e", mixer]
                else:
                    cmd = utils.which(mixer)
                Popen(cmd, shell=False)
        except Exception, err:
            log.Warn("Can\'t find mixer: %s" % str(err) )

    def get_mixer_name(self):
        if (self.config.getboolean(self.config.get_default_section(), "mixer_internal")):
            mixer = "voltilite-mixer"
        else:
            mixer = self.config.get(self.config.get_default_section(), "mixer")
        return mixer 
        
    def _mixer_get_pid(self):
        """ Get process id of mixer application """
        mixer = self.get_mixer_name()
        pid = Popen(utils.get_pid_app() + " " + os.path.basename(mixer),
                stdout=PIPE, shell=True).communicate()[0]
        if pid:
            try:
                return int(pid)
            except ValueError:
                return None
        return None

    def mixer_get_active(self):
        """ Returns status of mixer application """
        if self._mixer_get_pid():
            return True
        return False
