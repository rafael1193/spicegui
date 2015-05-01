# -*- coding: utf-8 -*-
#
# SpiceGUI
# Copyright (C) 2014-2015 Rafael Bailón-Ruiz <rafaelbailon@ieee.org>
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

from gi.repository import Gio, Gtk, GObject
import os.path


"""Create SPICE simulation commands"""
class AddSimulation(Gtk.Dialog):

    def __init__(self, parent, device_list):
        '''Init AddSimulation dialog.
        
        Args:
            parent: parent window.
            device_list: list of device names in netlist. Can't be None.
        '''
        Gtk.Dialog.__init__(self, "Add simulation statement", parent, use_header_bar=True)

        self.statement = None
        
        self.connect('response', self.on_response)

        # Load glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), 'data', 'add_simulation_dialog.glade'))
        self.notebook = self.builder.get_object('notebook')
        # connect after is required for get_current_page() returning the
        # current page, not that we're coming from
        self.notebook.connect_after('switch-page', self.on_notebook_switch_page)

        # notebook content references
        ## ac
        self.ac_variation_comboboxtext = self.builder.get_object('ac_variation_comboboxtext')
        self.ac_variation_comboboxtext.connect('changed', self.on_changed)
        self.ac_number_points_entry = self.builder.get_object('ac_number_points_entry')
        self.ac_number_points_entry.connect('notify::text', self.on_notify_text_event)
        self.ac_fstart_entry = self.builder.get_object('ac_fstart_entry')
        self.ac_fstart_entry.connect('notify::text', self.on_notify_text_event)
        self.ac_fstop_entry = self.builder.get_object('ac_fstop_entry')
        self.ac_fstop_entry.connect('notify::text', self.on_notify_text_event)
        ## dc
        self.dc_source_entry = self.builder.get_object('dc_source_entry')
        self.dc_source_entry.connect('notify::text', self.on_notify_text_event)
        self.dc_start_entry = self.builder.get_object('dc_start_entry')
        self.dc_start_entry.connect('notify::text', self.on_notify_text_event)
        self.dc_end_entry = self.builder.get_object('dc_end_entry')
        self.dc_end_entry.connect('notify::text', self.on_notify_text_event)
        self.dc_incr_entry = self.builder.get_object('dc_incr_entry')
        self.dc_incr_entry.connect('notify::text', self.on_notify_text_event)
        ## tran
        self.tran_tstep_entry = self.builder.get_object('tran_tstep_entry')
        self.tran_tstep_entry.connect('notify::text', self.on_notify_text_event)
        self.tran_tstop_entry = self.builder.get_object('tran_tstop_entry')
        self.tran_tstop_entry.connect('notify::text', self.on_notify_text_event)
        self.tran_tstart_entry = self.builder.get_object('tran_tstart_entry')
        self.tran_tstart_entry.connect('notify::text', self.on_notify_text_event)
        self.tran_tmax_entry = self.builder.get_object('tran_tmax_entry')
        self.tran_tmax_entry.connect('notify::text', self.on_notify_text_event)
        self.tran_uic_checkbutton = self.builder.get_object('tran_uic_checkbutton')
        self.tran_uic_checkbutton.connect('toggled', self.on_toggled)

        # setup dialog
        self.props.modal = True
        self.props.resizable = False
        self.set_default_response(Gtk.ResponseType.OK)
        self.add_button('_Cancel', Gtk.ResponseType.CANCEL)
        self.ok_button = self.add_button('_OK', Gtk.ResponseType.OK)
        self.ok_button.get_style_context().add_class('suggested-action');
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

        # setup content
        self.get_content_area().add(self.notebook)
        self.pages = {'ac':0, 'dc':1, 'tran':2}

        # Setup completion
        self.sources_entrycompletion = self.builder.get_object('sources_entrycompletion')
        
        self.completion_liststore = self.builder.get_object('completion_liststore')

        completion_iter = None
        for device in device_list:
            completion_iter = self.completion_liststore.insert_with_valuesv(-1,[0],[str(device)])
        
        self.sources_entrycompletion.set_model(self.completion_liststore)
        self.sources_entrycompletion.set_text_column(0)
        # Deactivate popup completion because is buggy (Gtk fault)
        self.sources_entrycompletion.set_popup_completion(False)
        
        self.show_all()
    
    def on_notebook_switch_page(self, notebook, page, page_num):
        self.entry_is_valid() 
        
    def on_notify_text_event(self, entry, string):
        self.entry_is_valid()
        
    def on_toggled(self, togglebutton):
        self.entry_is_valid()
        
    def on_changed(self, comboboxtext):
        self.entry_is_valid()
    
    def on_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            self.statement = self.generate_statement()
        else:
            self.statement = None
    
    def entry_is_valid(self):
        if self.notebook.get_current_page() == self.pages['ac'] and \
                    self.ac_number_points_entry.get_text() and \
                    self.ac_fstart_entry.get_text() and \
                    self.ac_fstop_entry.get_text():
            self.set_response_sensitive(Gtk.ResponseType.OK, True)
        elif self.notebook.get_current_page() == self.pages['dc'] and\
                self.dc_source_entry.get_text() and \
                self.dc_start_entry.get_text() and \
                self.dc_end_entry.get_text() and \
                self.dc_incr_entry.get_text():
            self.set_response_sensitive(Gtk.ResponseType.OK, True)
        elif self.notebook.get_current_page() == self.pages['tran'] and \
                self.tran_tstep_entry.get_text() and \
                self.tran_tstop_entry.get_text():
            self.set_response_sensitive(Gtk.ResponseType.OK, True)
        else:
            self.set_response_sensitive(Gtk.ResponseType.OK, False)
               
    def generate_statement(self):
        if self.notebook.get_current_page() == self.pages['ac']:
            return '.ac %s %s %s %s' % (
                        self.ac_variation_comboboxtext.get_active_id(),
                        self.ac_number_points_entry.get_text(),
                        self.ac_fstart_entry.get_text(),
                        self.ac_fstop_entry.get_text())
        elif self.notebook.get_current_page() == self.pages['dc']:
            return '.dc %s %s %s %s' % (
                        self.dc_source_entry.get_text(),
                        self.dc_start_entry.get_text(),
                        self.dc_end_entry.get_text(),
                        self.dc_incr_entry.get_text())
        elif self.notebook.get_current_page() == self.pages['tran']:
            return '.tran %s %s %s %s %s' % (
                        self.tran_tstep_entry.get_text(),
                        self.tran_tstop_entry.get_text(),
                        self.tran_tstart_entry.get_text(),
                        self.tran_tmax_entry.get_text(),
                        'uic' if self.tran_uic_checkbutton.get_active() else '')
        else:
            return None


if __name__ == '__main__':
    diag = AddSimulation(None, [])
    if diag.run() == int(Gtk.ResponseType.OK):
        print diag.statement
    diag.close()
