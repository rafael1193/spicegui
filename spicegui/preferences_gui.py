# -*- coding: utf-8 -*-
#
# SpiceGUI
# Copyright (C) 2014 Rafael Bailón-Ruiz <rafaelbailon@ieee.org>
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

from __future__ import print_function

import os.path

from gi.repository import Gio, Gtk

import constants

class Preferences(object):
    
    def __init__(self, parent):
       
        # Get window
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(constants.DOMAIN)
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "data", "preferences.glade"))

        window = self.builder.get_object('preferences_window')
        window.set_transient_for(parent)
        
        # Get gsettings reference
        settings = Gio.Settings.new(constants.GSETTINGS_BASE_KEY)
        
        ## Show legend setting
        show_legend_checkbutton = self.builder.get_object('show_legend_checkbutton')
        show_legend_checkbutton.set_active(settings.get_boolean("show-legend"))
        # If setting is changed externally
        settings.connect("changed::show-legend", self.on_show_legend_setting_changed, show_legend_checkbutton)
        # If checkbox is toggled
        show_legend_checkbutton.connect('toggled', self.on_show_legend_checkbutton_toggled, settings)
        
        ## Legend position setting
        legend_position_comboboxtext = self.builder.get_object('legend_position_comboboxtext')
        legend_position_comboboxtext.set_active_id(settings.get_string("legend-position"))
        # If setting is changed externally
        settings.connect("changed::legend-position", self.on_legend_position_setting_changed, legend_position_comboboxtext)
        # If combox item is selected
        legend_position_comboboxtext.connect('changed', self.on_legend_position_comboboxtext_changed, settings)
        
        ## Show grids setting
        show_grids_checkbutton = self.builder.get_object('show_grids_checkbutton')
        show_grids_checkbutton.set_active(settings.get_boolean("show-grids"))
        # If setting is changed externally
        settings.connect("changed::show-grids", self.on_show_grids_setting_changed, show_grids_checkbutton)
        # If checkbox is toggled
        show_grids_checkbutton.connect('toggled', self.on_show_grids_checkbutton_toggled, settings)
        
        # Show window
        window.connect_after('destroy', self.on_window_destroy)
        window.show_all()
        Gtk.main()
    
    def on_show_legend_setting_changed(self, settings, key, check_button):
        check_button.set_active(settings.get_boolean("show-legend"))
        
    def on_show_legend_checkbutton_toggled(self, button, settings):
        settings.set_boolean("show-legend", button.get_active())
    
    def on_legend_position_setting_changed(self, settings, key, check_button):
        check_button.set_active_id(settings.get_string("legend-position"))
        
    def on_legend_position_comboboxtext_changed(self, comboboxtext, settings):
        settings.set_string("legend-position", comboboxtext.get_active_id())
        
    def on_show_grids_setting_changed(self, settings, key, check_button):
        check_button.set_active(settings.get_boolean("show-grids"))
        
    def on_show_grids_checkbutton_toggled(self, button, settings):
        settings.set_boolean("show-grids", button.get_active())
                                  
    def on_window_destroy(self, widget, data=None):
        Gtk.main_quit()

if __name__ == "__main__":
    app = App() 
