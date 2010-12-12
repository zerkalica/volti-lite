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

class Icons:
    @staticmethod
    def get_icon_name_by_volume(volume):
        """ Returns icon name for current volume """
        if not volume:
            icon = "audio-volume-muted"
        elif volume <= 33:
            icon = "audio-volume-low"
        elif volume <= 66:
            icon = "audio-volume-medium"
        elif volume > 66:
            icon = "audio-volume-high"
        return icon

    @staticmethod    
    def get_volume_name(volume, muted=False):
        if (volume == 0 or muted):
            volume = _("Muted")
        return volume
    

    @staticmethod
    def get_icon_themes(res_dir):
        themes = ["default"]
        icons_dir = os.path.join(res_dir, "icons")
        try:
            for file in os.listdir(icons_dir):
                if os.path.isdir(os.path.join(icons_dir, file)):
                    if not file.startswith("."):
                        themes.append(file)
        except OSError:
            pass
        return themes

        