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

from debug import log
from abc import abstractmethod
import gobject
import alsaaudio as alsa

class MixerChannel:
    def __init__(self, card_index, control = "Master", cid = 0, emulate_mute = False):
        MixerChannel.update(self, card_index, control, cid, emulate_mute)
        
    def __del__(self):
        self.close()
        
    def update(self, card_index, control, cid , emulate_mute = False):
        
        self.channel = alsa.MIXER_CHANNEL_ALL
        self.mixer = None
        self._lock = True
        self._muted = False
        self.last_mute = False
        self.channel_count = 1
        
        self.card_index = card_index
        self.control = control
        self.cid = cid
        self.emulate_mute = emulate_mute
        
        self.reopen()
        
        self.last_volume = self.get_volume()
        self.old_volume = self.last_volume
        self.channel_count = len(self.last_volume)
        
    def get_status_info(self):
        """ Returns status information """
        volume = self.get_volume()
        muted = self.get_mute()
        
        if ( not volume[0] or muted ):
            var = ""
        else:
            var = "%"
            
        card_name = self.mixer.cardname()
        mixer_name = self.mixer.mixer()
        return [volume, muted, var, card_name, mixer_name]
    
    def reopen(self):
        self.close()
        try:
            self.mixer = alsa.Mixer(control=self.control, cardindex = self.card_index, id = self.cid)
        except Exception, err:
            log.Error("Can't get mixer: %s" % (str(err)) )

    def close(self):
        if (self.mixer):
            self.mixer.close()
            self.mixer = None
            
    def set_rec(self, value):
        
        try:
            self.mixer.setrec(int(value))
        except:
            log.Warn("Can't set rec")
        

    def set_mute(self, value):
        if ( not self.emulate_mute ):
            
            try:
                self.mixer.setmute(int(value))
                assert self.get_mute() == value
            except:
                log.Notice("set emulate to on")
                self.emulate_mute  = True
            
                
        if ( self.emulate_mute ):
            if ( value ):
                self._muted = False
                self.old_volume = self.mixer.getvolume()
                
                volume = [0] * self.get_channel_count(); 
                for i, vol in enumerate(volume):
                    self.mixer.setvolume(vol, i)
                    
                self._muted = True
            else:
                self._muted = False
                for i, vol in enumerate(self.old_volume):
                    self.mixer.setvolume(vol, i)
                    
        self.last_mute = value

    def set_lock(self, value):
        log.Notice("sets lock for %s to %s" % (self.control, value) )
        self._lock = value

    def set_volume(self, volume, channel = None):
        """ Set the playback volume """
        if ( channel == None ):
            volume = [volume] * self.get_channel_count(); 
            for i, vol in enumerate(volume):
                self.mixer.setvolume(vol, i)
                self.last_volume[i] = vol
        else:
            self.mixer.setvolume(volume, channel)
            self.last_volume[channel] = volume
        
    def get_rec(self):
        ret = None
        try:
            record = self.mixer.getrec()
            ret = record[0]
        except:
            pass
        
        return ret
    
    def get_mute(self):
        mute = False
        if (not self.emulate_mute):
            try:
                mute = self.mixer.getmute()[0] == 1
            except:
                volume = self.get_volume()
                if ( isinstance(volume, list) ):
                    volume = int(volume[0]) 
                self._muted = volume == 0
        if (self.emulate_mute):
            mute = self._muted
        return mute

    def get_lock(self):
        return self._lock
    
    def is_volume_changed(self, volume):
        return self.last_volume != volume
        
    def is_mute_changed(self, mute):
        return self.last_mute != mute
        
    def get_volume(self):
        """ Get the current sound card setting for specified channel """
        if (self._muted):
            volume = self.old_volume
        else:
            try:
                volume = self.mixer.getvolume()
            except Exception, err:
                log.Warn("Can't get volume: %s" % (str(err)) )
                volume = [0] * self.get_channel_count()
            
        return volume
    
    def get_channel_count(self):
        return self.channel_count
    
    def get_volumecap(self):
        vc = None
        
        try:
            vc = self.mixer.volumecap()
        except:
            log.Warn("Can't get volumecap")
            vc = None
        return vc

    def get_descriptors(self):
        """ Returns file descriptors """
        desc = None
        
        try:
            desc = self.mixer.polldescriptors()[0]
        except:
            desc = [None, None]
        
        return desc

class CardInfo():
    @staticmethod
    def get_cards():
        """ Returns cards list """
        cards = []
        acards = alsa.cards()
        log.Notice("getting card list", 1)
        for index, card in enumerate(acards):
            try:
                assert len (CardInfo.get_mixers(index)) > 0
            except IndexError, err:
                log.Warn("Card error: %s" % str(err))
                cards.append(None)
            else:
                cards.append(card)
        return cards
    
    @staticmethod
    def get_mixers(card_index=0):
        """ Returns mixers list """
        mixers_tmp = []
        mixers_params = []
        for control in alsa.mixers(card_index):
            cid = mixers_tmp.count(control)
            mixer = MixerChannel(card_index, control, cid)
            cap = mixer.get_volumecap()
            if ( cap ):
                #if 'Playback Volume' in cap or 'Joined Volume' in cap:
                item = [control, cid]
                mixers_params.append(item)
                mixers_tmp.append(control)
            del mixer
        return mixers_params

class MixerHandler:    
    @staticmethod
    def connect(handler):
        log.Notice("connect handler", 1)
        return gobject.timeout_add(200, handler)
    
    @staticmethod
    def disconnect(handle):
        log.Notice("disconnect handler", 1)
        gobject.source_remove(handle)

class MixerControlAbstract(MixerChannel):
    def __init__(self, card_index = 0, control = "Master", cid = 0, emulate_mute = False):
        MixerChannel.__init__(self, card_index, control, cid, emulate_mute)
        self.load()
    
    def update(self, card_index = 0, control = "Master", cid = 0, emulate_mute = False):
        MixerChannel.update(self, card_index, control, cid, emulate_mute)
        self.load()
            
    @abstractmethod    
    def on_volume_changed(self, volume):
        pass
    @abstractmethod
    def on_mute_changed(self, mute):
        pass
    @abstractmethod
    def on_any_changed(self, volume, mute):
        pass
    
    def on_change(self):
        #@bug: alsa needs reopen mixer if volume changed by side events
        self.reopen()
        volume = self.get_volume()
        mute = self.get_mute()
        volume_changed = self.is_volume_changed(volume)
        mute_changed = self.is_mute_changed(mute)
        if ( volume_changed or mute_changed ):
            log.Notice("Volume changed: %s:%s, %s->%s, mute=%s->%s" % (self.card_index, self.control, self.last_volume, volume, self.last_mute, mute))

            #disable feedback events from slider and menu
            if(volume_changed):
                self.on_volume_changed(volume)
            if(mute_changed):
                self.on_mute_changed(mute)
            
            self.on_any_changed(volume, mute)
            
            self.last_mute = mute
            self.last_volume = volume
        return True

    def save(self):
        pass
    
    def load(self):
        pass

class MixerControlLocableAbstract(MixerControlAbstract):
    def __init__(self, config, card_index = 0, control = "Master", cid = 0, emulate_mute = False):
        self.config = config
        self.set_mixer_section(card_index, control, cid)
        MixerControlAbstract.__init__(self, card_index, control, cid, emulate_mute)

    def set_mixer_section(self, card_index, control, cid):
        self.mixer_section = self._get_mixer_section_name(card_index)
        self.key = control + '_' + str(cid)
        
    def update(self, card_index = 0, control = "Master", cid = 0, emulate_mute = False):
        self.set_mixer_section(card_index, control, cid)
        MixerControlAbstract.update(self, card_index, control, cid, emulate_mute)
        
    def _get_mixer_section_name(self, card_index):
        return "card-mixer-%s" % card_index
        
    def save(self):
        if ( not self.config.has_section(self.mixer_section) ):
            self.config.add_section(self.mixer_section)
        lock = self.get_lock()
        log.Notice("control = %s lock = %s" % (self.control, lock))
        if ( not self.config.has_option(self.mixer_section, self.key) or lock != self.config.getboolean(self.mixer_section, self.key) ):
            self.config.set(self.mixer_section, self.key, lock)

    def load(self):
        if ( self.config.has_section(self.mixer_section) ):
            if ( self.config.has_option(self.mixer_section, self.key) ):
                self.set_lock(self.config.getboolean(self.mixer_section, self.key))

class MixerAbstract():
    def __init__(self, config, card_index):
        self.config = config
        self.controls = []
        self.card_index = card_index
        self.init()
        #get_descriptors + gobject.io_add_watch is bad choice, becouse it's events start repeats infinitely after first event
        #the best way is snd_mixer_set_callback, but it not implemented in pyalsa
        #so get alsa status in timer

    def __del__(self):
        log.Notice("deleting mixer")
        #@TODO: why del control is not working ?
        for control in self.controls:
            del control
            
    def add_control(self, control):
        self.controls.append( control )
        
    def del_control(self, control):
        self.controls.remove(control)
        del control
                
    def on_change(self):
        for control in self.controls:
            control.on_change()
        return True
            
    @abstractmethod
    def init(self):
        pass
    
    def save(self):
        for control in self.controls:
            control.save()

    def load(self):
        for control in self.controls:
            control.load()
