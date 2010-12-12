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
import gtk
import pango
from mixerbase import CardInfo
import icons
import gobject
from debug import log

class Preferences:
    """ Preferences window """
    
    mixers = ["aumix", "alsamixer", "alsamixergui", "gamix",
           "gmixer", "gnome-alsamixer", "gnome-volume-control"]

    def __init__(self, config, on_close_hook, on_update_hook):
        """ Constructor """
        self.config = config
        self.card_index = self.config.getint(self.config.get_default_section(), "card_index")
        
        self.on_close_hook = on_close_hook
        self.on_update_hook = on_update_hook
        
        self.init_builder()
        self.init_card_combobox()
        self.init_treeview()
        self.window.show_all()
        log.Notice("init preferences")
        
    def __del__(self):
        log.Notice("desctruct")
                
    def show(self):
        self.window.present()
        
    def close(self, widget=None):
        """ Close preferences window """
        log.Notice("closed")
        self.window.destroy()
        self.on_close_hook()
        
    def on_button_close(self, widget = None):
        log.Notice("emit destroy")
        self._set_body()
        self.update_main()
        self.window.emit("destroy")
    
    def update_main(self):
        self.on_update_hook()
        
    def _set_body(self):
        start, end = self.notify_body_text.get_buffer().get_bounds()
        body = self.notify_body_text.get_buffer().get_text(start, end)
        self.config.set(self.config.get_default_section(), "notify_body", body)

    def init_builder(self):
        """ Initialize gtk.Builder """
        self.glade = os.path.join(self.config.res_dir, "preferences.glade")
        self.tree = gtk.Builder()
        self.tree.set_translation_domain(self.config.app_name)
        self.tree.add_from_file(self.glade)
        default = self.config.get_default_section()

        self.version_label = self.tree.get_object("version_label")
        self.version_label.set_text("%s %s" % (
            self.config.app_name.capitalize(), self.config.app_version))

        self.window = self.tree.get_object("window")
        self.window.connect("destroy", self.close)
        icon_theme = gtk.icon_theme_get_default()
        
        if icon_theme.has_icon("multimedia-volume-control"):
            self.window.set_icon_name("multimedia-volume-control")
        else:
            file = os.path.join(
                    self.config.res_dir, "icons", "multimedia-volume-control.svg")
            self.window.set_icon_from_file(file)

        self.button_close = self.tree.get_object("button_close")
        self.button_close.connect("clicked", self.on_button_close)

        self.button_browse = self.tree.get_object("button_browse")
        self.button_browse.connect("clicked", self.on_browse_button_clicked)

        self.mixer_entry = self.tree.get_object("mixer_entry")
        self.mixer_entry.set_text(self.config.get(default, "mixer"))
        self.mixer_entry.connect_after("changed", self.on_entry_changed)

        self.scale_spinbutton = self.tree.get_object("scale_spinbutton")
        self.scale_spinbutton.set_value((self.config.getfloat(default, "scale_increment")))
        self.scale_spinbutton.connect("value_changed", self.on_scale_spinbutton_changed)

        self.tooltip_checkbutton = self.tree.get_object("tooltip_checkbutton")
        self.tooltip_checkbutton.set_active(self.config.getboolean(default, "show_tooltip"))
        self.tooltip_checkbutton.connect("toggled", self.on_tooltip_toggled)

        self.terminal_checkbutton = self.tree.get_object("terminal_checkbutton")
        self.terminal_checkbutton.set_active(self.config.getboolean(default, "run_in_terminal"))
        self.terminal_checkbutton.connect("toggled", self.on_terminal_toggled)

        self.draw_value_checkbutton = self.tree.get_object("draw_value_checkbutton")
        self.draw_value_checkbutton.set_active(self.config.getboolean(default, "scale_show_value"))
        self.draw_value_checkbutton.connect("toggled", self.on_draw_value_toggled)

        self.notify_checkbutton = self.tree.get_object("notify_checkbutton")
        self.notify_checkbutton.set_active(self.config.getboolean(default, "show_notify"))
        self.notify_checkbutton.connect("toggled", self.on_notify_toggled)

        self.notify_body_text = self.tree.get_object("notify_body_text")
        self.notify_body_text.get_buffer().set_text(self.config.get(default, "notify_body"))

        self.position_checkbutton = self.tree.get_object("position_checkbutton")
        self.position_checkbutton.set_active(self.config.getboolean(default, "notify_position"))
        self.position_checkbutton.connect("toggled", self.on_position_toggled)

        self.timeout_spinbutton = self.tree.get_object("timeout_spinbutton")
        self.timeout_spinbutton.set_value(self.config.getfloat(default, "notify_timeout"))
        self.timeout_spinbutton.connect("value_changed", self.on_timeout_spinbutton_changed)

        self.mixer_internal_checkbutton = self.tree.get_object("mixer_internal_checkbutton")
        self.mixer_internal_checkbutton.set_active(self.config.getboolean(default, "mixer_internal"))
        self.mixer_internal_checkbutton.connect("toggled", self.on_mixer_internal_toggled)

        self.mixer_values_checkbutton = self.tree.get_object("mixer_values_checkbutton")
        self.mixer_values_checkbutton.set_active(self.config.getboolean(default, "mixer_show_values"))
        self.mixer_values_checkbutton.connect("toggled", self.on_mixer_values_toggled)

        self.mute_radiobutton = self.tree.get_object("radiobutton_mute")
        self.mixer_radiobutton = self.tree.get_object("radiobutton_mixer")
        toggle = self.config.get(default, "toggle")
        if toggle == "mute":
            self.mute_radiobutton.set_active(True)
        elif toggle == "mixer":
            self.mixer_radiobutton.set_active(True)
        self.mute_radiobutton.connect("toggled", self.on_radio_mute_toggled)
        self.mixer_radiobutton.connect("toggled", self.on_radio_mixer_toggled)

        self.set_notify_sensitive(self.config.getboolean(default, "show_notify"))
        self.set_mixer_sensitive(self.config.getboolean(default, "mixer_internal"))

    def init_card_combobox(self):
        """ Initialize combobox with list of audio cards """
        icon_theme = gtk.icon_theme_get_default()
        if icon_theme.has_icon("audio-card"):
            icon = icon_theme.load_icon(
                    "audio-card", 22, flags=gtk.ICON_LOOKUP_FORCE_SVG)
        else:
            file = os.path.join(
                    self.config.res_dir, "icons", "audio-card.svg")
            pixbuf = gtk.gdk.pixbuf_new_from_file(file)
            icon = pixbuf.scale_simple(22, 22, gtk.gdk.INTERP_BILINEAR)

        self.combo_model = gtk.ListStore(int, gtk.gdk.Pixbuf, str)
        for index, card in enumerate(CardInfo.get_cards()):
            if card is not None:
                self.combo_model.append([index, icon, card])
        
        default = self.config.get_default_section()
        
        card_combobox = self.tree.get_object("card_combobox")
        card_combobox.set_model(self.combo_model)
        card_combobox.set_active(self.config.getint(default, "card_index"))

        cell1 = gtk.CellRendererPixbuf()
        cell1.set_property("xalign", 0)
        cell1.set_property("xpad", 3)
        card_combobox.pack_start(cell1, False)
        card_combobox.add_attribute(cell1, "pixbuf", 1)

        cell2 = gtk.CellRendererText()
        cell2.set_property("xpad", 10)
        card_combobox.pack_start(cell2, True)
        card_combobox.set_attributes(cell2, text=2)

        card_combobox.connect("changed", self.on_card_combobox_changed)

    def init_treeview(self):
        """ Initialize treeview with mixers """
        card_index = self.config.getint(self.config.get_default_section(), "card_index")
        
        self.liststore = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_INT)
        self.set_liststore(card_index, self.liststore)
        
        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.set_headers_visible(False)

        cell1 = gtk.CellRendererToggle()
        cell1.set_radio(True)
        cell1.set_property("activatable", True)
        cell1.connect('toggled', self.on_treeview_toggled, self.liststore)
        column1 = gtk.TreeViewColumn()
        column1.pack_start(cell1)
        column1.add_attribute(cell1, 'active', 0)
        self.treeview.append_column(column1)

        cell2 = gtk.CellRendererText()
        column2 = gtk.TreeViewColumn()
        column2.pack_start(cell2)
        column2.add_attribute(cell2, 'weight', 1)
        column2.add_attribute(cell2, 'text', 2)
        self.treeview.append_column(column2)
        
        cell3 = gtk.CellRendererText()
        column3 = gtk.TreeViewColumn()
        column3.pack_start(cell3)
        column3.add_attribute(cell3, 'text', 3)
        self.treeview.append_column(column3)
        
        scrolledwindow = self.tree.get_object("scrolledwindow")
        scrolledwindow.add(self.treeview)

    def on_browse_button_clicked(self, widget=None):
        """ Callback for browse_button_clicked event """
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        dialog = gtk.FileChooserDialog(
                title=_("Choose external mixer"),
                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=buttons)
        dialog.set_current_folder("/usr/bin")
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_show_hidden(False)

        file_filter_mixers = gtk.FileFilter()
        file_filter_mixers.set_name(_("Sound Mixers"))
        file_filter_mixers.add_custom(gtk.FILE_FILTER_FILENAME, self.custom_mixer_filter)
        file_filter_all = gtk.FileFilter()
        file_filter_all.set_name(_("All files"))
        file_filter_all.add_pattern("*")
        dialog.add_filter(file_filter_mixers)
        dialog.add_filter(file_filter_all)

        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()

        while gtk.events_pending():
            gtk.main_iteration(False)

        if response == gtk.RESPONSE_OK:
            self.mixer_entry.set_text(filename)
            self.config.set(self.config.get_default_section(), "mixer", filename)
            return filename
        elif response == gtk.RESPONSE_CANCEL:
            return None

    def custom_mixer_filter(self, filter_info=None, data=None):
        """ Custom filter with names of common mixer apps """
        if filter_info[2] in self.mixers:
            return True
        return False

    def on_card_combobox_changed(self, widget=None):
        """ Callback for card_combobox_changed event """
        model = widget.get_model()
        iter = widget.get_active_iter()
        self.card_index = model.get_value(iter, 0)
        self.set_liststore(self.card_index, self.liststore)
        
    def set_liststore(self, card_index, liststore):
        card_index_cmp = self.config.getint(self.config.get_default_section(), "card_index")
        default_mixer = self.config.get(self.config.get_card_section(), "control")
        default_cid = self.config.getint(self.config.get_card_section(), "cid")
        mixers = CardInfo.get_mixers(card_index)
        liststore.clear()
        log.Notice("default_mixer = %s, default_cid = %i" % (default_mixer, default_cid))
        for mixer, cid in mixers:
            active = (card_index == card_index_cmp and mixer == default_mixer and cid == default_cid )
            weight = pango.WEIGHT_NORMAL
            if active:
                weight = pango.WEIGHT_BOLD
            liststore.append([active, weight, mixer, cid])

    def on_treeview_toggled(self, cell, path, model):
        """ Callback for treeview_toggled event """
        iter = model.get_iter_from_string(path)
        active = model.get_value(iter, 0)
        if not active:
            model.foreach(self.radio_toggle)
            model.set(iter, 0, not active)
            model.set(iter, 1, pango.WEIGHT_BOLD)
            mixer = model.get_value(iter, 2)
            cid = model.get_value(iter, 3)
            log.Notice("Tree view toggled")
            self.config.set_card_index(self.card_index)
            self.config.set_card_mixer(mixer, cid)
            self.update_main()

    def radio_toggle(self, model, path, iter):
        """ Toggles radio buttons status """
        active = model.get(iter, 0)
        if active:
            model.set(iter, 0, not active)
            model.set(iter, 1, pango.WEIGHT_NORMAL)

    def on_scale_spinbutton_changed(self, widget):
        """ Callback for scale_spinbutton_changed event """
        scale_increment = widget.get_value()
        self.config.set(self.config.get_default_section(), "scale_increment", scale_increment)
        self.update_main()

    def on_tooltip_toggled(self, widget):
        """ Callback for tooltip_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "show_tooltip", active)
        self.update_main()

    def on_draw_value_toggled(self, widget):
        """ Callback for draw_value_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "scale_show_value", active)
        self.update_main()

    def on_terminal_toggled(self, widget):
        """ Callback for terminal_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "run_in_terminal", active)

    def on_entry_changed(self, widget):
        """ Callback for entry_changed event """
        mixer = widget.get_text()
        self.config.set(self.config.get_default_section(), "mixer", mixer)

    def on_mixer_internal_toggled(self, widget):
        """ Callback for mixer_internal_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "mixer_internal", active)
        self.set_mixer_sensitive(active)
        self.update_main()

    def on_mixer_values_toggled(self, widget):
        """ Callback for mixer_values_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "mixer_show_values", active)

    def on_radio_mute_toggled(self, widget):
        """ Callback for radio_mute_toggled event """
        if widget.get_active():
            self.config.set(self.config.get_default_section(), "toggle", "mute")

    def on_radio_mixer_toggled(self, widget):
        """ Callback for radio_mixer_toggled event """
        if widget.get_active():
            self.config.set(self.config.get_default_section(), "toggle", "mixer")

    def on_notify_toggled(self, widget):
        """ Callback for notify_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "show_notify", active)
        self.set_notify_sensitive(active)
        self.update_main()

    def on_position_toggled(self, widget):
        """ Callback for position_toggled event """
        active = widget.get_active()
        self.config.set(self.config.get_default_section(), "notify_position", active)
        self.update_main()

    def on_timeout_spinbutton_changed(self, widget):
        """ Callback for spinbutton_changed event """
        timeout = widget.get_value()
        self.config.set(self.config.get_default_section(), "notify_timeout", timeout)

    def set_mixer_sensitive(self, active):
        """ Set widgets sensitivity """
        self.mixer_values_checkbutton.set_sensitive(active)
        self.mixer_entry.set_sensitive(not active)
        self.button_browse.set_sensitive(not active)
        self.terminal_checkbutton.set_sensitive(not active)

    def set_notify_sensitive(self, active):
        """ Set widgets sensitivity """
        self.timeout_spinbutton.set_sensitive(active)
        self.position_checkbutton.set_sensitive(active)
        self.notify_body_text.set_sensitive(active)
