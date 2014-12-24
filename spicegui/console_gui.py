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

from gi.repository import Gtk, Pango

class ConsoleOutputWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_default_size(640, 480)

        # headerbar
        self.hb = Gtk.HeaderBar()
        self.hb.props.show_close_button = True
        self.hb.set_title("Console output")
        self.set_titlebar(self.hb)
        
        # Content
        self.scrolled = Gtk.ScrolledWindow()
        self.text_view = Gtk.TextView(buffer=Gtk.TextBuffer())

        font_desc = Pango.FontDescription('monospace')
        if font_desc:
            self.text_view.modify_font(font_desc)

        self.scrolled.add(self.text_view)
        self.add(self.scrolled)

        # Connect signals
        self.connect_after('destroy', self.on_window_destroy)
    
    def insert_text(self, text):
        self.text_view.props.buffer.insert_at_cursor(text)
    
    def clear_buffer(self):
        start_iter = self.text_view.props.buffer.get_start_iter()
        end_iter = self.text_view.props.buffer.get_end_iter()
        self.text_view.props.buffer.delete(start_iter, end_iter)
    
    def set_subtitle(self, text):
        self.hb.set_subtitle(text)
    
    def on_window_destroy(self, widget, data=None):
        Gtk.main_quit()

if __name__ == "__main__":
    window = ConsoleOutputWindow()
    window.show_all()
    window.insert_text("test\n  Test\tTEST")
    window.clear_buffer()
    window.set_subtitle("Spawned command")
    Gtk.main()
