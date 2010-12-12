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
from debug import log
from subprocess import Popen, PIPE

class utils:

    @staticmethod
    def which(prog):
        """ Equivalent of unix which command """
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(prog)
        if fpath:
            if is_exe(prog):
                return prog
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                filename = os.path.join(path, prog)
                if is_exe(filename):
                    return filename
        return None

    @staticmethod
    def find_term():
        term = os.getenv("TERM")
        if (term == "linux" or term is None):
            term = utils.which("x-terminal-emulator")
            if(not term):
                if (utils.which("gconftool-2")):
                    term = Popen(["gconftool-2", "-g", "/desktop/gnome/applications/terminal/exec"], 
                                 stdout=PIPE).communicate()[0].strip()
                else:
                    term = utils.which("xterm")
                    if (not term):
                        term = utils.which("rxvt")
                        if (not term):
                            term = utils.which("urxvt")
                            if (not term):
                                log.Warn("No any terminals found")
                                term = None
        return term

    @staticmethod
    def get_pid_app():
        if utils.which("pidof"):
            pid_app = "pidof -x"
        elif utils.which("pgrep"):
            pid_app = "pgrep"
        else:
            log.Warn("No pid app found")
            pid_app = None
        return pid_app
    
