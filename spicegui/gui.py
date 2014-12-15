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

from gi.repository import Gtk, Gdk, Gio, GtkSource, Pango
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

import os
import os.path

import ngspice_simulation
import running_dialog


class MainWindow(Gtk.ApplicationWindow):

    gear_menu_xml = """
    <?xml version="1.0" encoding="UTF-8"?>
    <interface domain="spicegui">
    <!-- interface-requires gtk+ 3.6 -->
        <menu id="gearmenu-overview">
            <section>
                <item>
                    <attribute name="label" translatable="yes">_Save</attribute>
                    <attribute name="action">win.save</attribute>
                    <attribute name="accel">&lt;Primary&gt;S</attribute>
                </item>
                <item>
                    <attribute name="label" translatable="yes">S_ave as...</attribute>
                    <attribute name="action">win.save-as</attribute>
                </item>
            </section>
            <section>
                <item>
                    <attribute name="label" translatable="yes">_Close</attribute>
                    <attribute name="action">win.close</attribute>
                </item>
            </section>
        </menu>
        <menu id="gearmenu-simulation">
            <section>
                <item>
                    <attribute name="label" translatable="yes">_Save plot</attribute>
                    <attribute name="action">win.save-plot</attribute>
                </item>
                <item>
                    <attribute name="label" translatable="yes">Save data</attribute>
                    <attribute name="action">win.save-data</attribute>
                </item>
            </section>
            <section>
                <item>
                    <attribute name="label" translatable="yes">Plot preferences</attribute>
                    <attribute name="action">win.plot-preferences</attribute>
                </item>
            </section>
            <section>
                <item>
                    <attribute name="label" translatable="yes">_Close</attribute>
                    <attribute name="action">win.close</attribute>
                </item>
            </section>
        </menu>
    </interface>
    """

    insert_menu_xml = """
    <?xml version="1.0" encoding="UTF-8"?>
    <interface domain="spicegui">
    <!-- interface-requires gtk+ 3.6 -->
        <menu id="insertmenu">
            <section>
                <item>
                    <attribute name="label" translatable="yes">._ac</attribute>
                    <attribute name="action">win.insert-ac</attribute>
                </item>
                <item>
                    <attribute name="label" translatable="yes">._dc</attribute>
                    <attribute name="action">win.insert-dc</attribute>
                </item>
                <item>
                    <attribute name="label" translatable="yes">._tran</attribute>
                    <attribute name="action">win.insert-tran</attribute>
                </item>
            </section>
            <section>
                <item>
                    <attribute name="label" translatable="yes">._print</attribute>
                    <attribute name="action">win.insert-print</attribute>
                </item>
            </section>
            <section>
                <item>
                    <attribute name="label" translatable="yes">._model</attribute>
                    <attribute name="action">win.insert-model</attribute>
                </item>
                <item>
                    <attribute name="label" translatable="yes">._lib</attribute>
                    <attribute name="action">win.insert-lib</attribute>
                </item>
                <item>
                    <attribute name="label" translatable="yes">._include</attribute>
                    <attribute name="action">win.insert-include</attribute>
                </item>
            </section>
        </menu>
    </interface>
    """

    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_default_size(900, 600)

        self.circuit = None
        self.netlist_file_path = None
        self.file_monitor = None
        self._create_menu_models()

        ##########
        #headerbar
        self.hb = Gtk.HeaderBar()
        self.hb.props.show_close_button = True

        if self.csd_are_supported() == True:
            self.set_titlebar(self.hb)
        else: #disable headerbar as titlebar if not supported
            self.no_csd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.no_csd_box.pack_start(self.hb, False, False, 0)
            self.hb.props.show_close_button = False
            self.add(self.no_csd_box)

        ## Right side of headerbar
        self.hb_rbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._add_insert_button()
        self._add_simulate_button()
#        self._add_save_button() #Save button is no loger needed
        self._add_gear_button()

        self.hb.pack_end(self.hb_rbox)

        ## Left side of headerbar
#        self._add_back_button()
#        self.back_button.props.visible = False
        self._add_arrow_buttons()
        self._add_load_button()

#        self.simulate_button.props.sensitive = False

        ########
        #Content
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(500)

        ## Overview stack
        self.overview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.source_view = None
        self._open_state("new")


        self.infobar = None
        self.stack.add_titled(self.overview_box, "overview", "Circuit")

        ## Simulation stack
        self.simulation_box = Gtk.Box()
        self.canvas = Gtk.DrawingArea()
        self.simulation_box.pack_start(self.canvas, True, True, 0)
        self.stack.add_titled(self.simulation_box, "simulation", "Simulation")

        if self.csd_are_supported() == True:
            self.add(self.stack)
        else: #disable headerbar as titlebar if not supported
            self.no_csd_box.pack_end(self.stack, True, True, 0)

        self.overview_view()
        self.connect_after('destroy', self._on_destroy)
    
    def _open_state(self, state="opened"):
        """
        show sourceview state="opened" or suggest opening a file state="new"
        """
        if state == "opened":
            for child in self.overview_box.get_children():
                self.overview_box.remove(child)
            self.source_scrolled = Gtk.ScrolledWindow(None, None)
            self.source_scrolled.set_hexpand(True)
            self.source_scrolled.set_vexpand(True)
    
            self.source_buffer = GtkSource.Buffer()
            self.source_buffer.set_highlight_syntax(True)
            self.source_buffer.set_language(GtkSource.LanguageManager.get_default().get_language("spice-netlist"))
            self.sourceview = GtkSource.View()
            font_desc = Pango.FontDescription('monospace')
            if font_desc:
                self.sourceview.modify_font(font_desc)
            self.sourceview.set_buffer(self.source_buffer)
            self.sourceview.set_show_line_numbers(True)
            self.source_scrolled.add(self.sourceview)
            self.overview_box.pack_end(self.source_scrolled, True, True, 0)
            self.overview_box.show_all()
            self.insert_button.props.sensitive = False
            self.simulate_button.props.sensitive = False
        elif state == "new":
            if self.source_view is not None:
                self.overview_box.remove(self.source_scrolled)
                self.source_view = None
            else:
                self.emptyGrid = Gtk.Grid(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, column_spacing=12, margin=30)
                self.overview_box.add(self.emptyGrid);
                emptyPageImage = Gtk.Image(icon_name='document-open-symbolic', icon_size=Gtk.IconSize.DIALOG)
                emptyPageImage.get_style_context().add_class('dim-label')
                self.emptyGrid.add(emptyPageImage)
                emptyPageDirections = Gtk.Label(label="Use the <b>Open</b> button to load a circuit", use_markup=True, max_width_chars=30, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER )
                emptyPageDirections.get_style_context().add_class('dim-label');
                self.emptyGrid.add(emptyPageDirections);
                self.emptyGrid.show_all();
                self.overview_box.pack_end(self.emptyGrid, True, True, 0)
                self.insert_button.props.sensitive = False
                self.simulate_button.props.sensitive = False
                self.forward_button.props.sensitive = False # TODO: let see why this is not effective...
                # TODO: Disable "save" action -> self.actions ... .set_enable(False)

    def _create_menu_models(self):
        # gear_menu overview xml #
        ## Create menu model
        builder = Gtk.Builder()
        builder.add_from_string(self.gear_menu_xml)
        self.gearmenu_overview = builder.get_object('gearmenu-overview')

        ## Bind actions
        save_action = Gio.SimpleAction.new("save", None)
        save_action.connect("activate", self.save_cb)
        self.add_action(save_action)

        close_action = Gio.SimpleAction.new("close", None)
        close_action.connect("activate", self.close_cb)
        self.add_action(close_action)

        # gear_menu simulation xml #
        ## Create menu model
        builder = Gtk.Builder()
        builder.add_from_string(self.gear_menu_xml)
        self.gearmenu_simulation = builder.get_object('gearmenu-simulation')

        ## Bind actions
        save_plot_action = Gio.SimpleAction.new("save-plot", None)
        save_plot_action.connect("activate", self.save_plot_cb)
        self.add_action(save_plot_action)

        save_data_action = Gio.SimpleAction.new("save-data", None)
        save_data_action.connect("activate", self.save_data_cb)
        self.add_action(save_data_action)

        # insert_menu_xml #
        ## Create menu model
        builder = Gtk.Builder()
        builder.add_from_string(self.insert_menu_xml)
        self.insertmenu = builder.get_object('insertmenu')

        ## Bind actions
        insert_ac_action = Gio.SimpleAction.new("insert-ac", None)
        insert_ac_action.connect("activate", self.insert_ac_cb)
        self.add_action(insert_ac_action)

        insert_dc_action = Gio.SimpleAction.new("insert-dc", None)
        insert_dc_action.connect("activate", self.insert_dc_cb)
        self.add_action(insert_dc_action)

        insert_tran_action = Gio.SimpleAction.new("insert-tran", None)
        insert_tran_action.connect("activate", self.insert_tran_cb)
        self.add_action(insert_tran_action)

        insert_print_action = Gio.SimpleAction.new("insert-print", None)
        insert_print_action.connect("activate", self.insert_print_cb)
        self.add_action(insert_print_action)

        insert_model_action = Gio.SimpleAction.new("insert-model", None)
        insert_model_action.connect("activate", self.insert_model_cb)
        self.add_action(insert_model_action)

        insert_lib_action = Gio.SimpleAction.new("insert-lib", None)
        insert_lib_action.connect("activate", self.insert_lib_cb)
        self.add_action(insert_lib_action)

        insert_include_action = Gio.SimpleAction.new("insert-include", None)
        insert_include_action.connect("activate", self.insert_include_cb)
        self.add_action(insert_include_action)

    def save_cb(self, action, parameters):
        self.on_save_button_clicked_overview(None)

    def save_plot_cb(self, action, parameters):
        dialog = Gtk.FileChooserDialog("Save plot", self, Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        png_filter = Gtk.FileFilter()
        png_filter.set_name("Portable Network Graphics")
        png_filter.add_mime_type("image/png")
        dialog.add_filter(png_filter)

        svg_filter = Gtk.FileFilter()
        svg_filter.set_name("Scalable Vector Graphics")
        svg_filter.add_mime_type("image/svg+xml")
        dialog.add_filter(svg_filter)
      
        dialog.set_current_name(self.hb.get_title()+" - "+self.simulation_output.analysis)

        response = dialog.run()
        dialog.set_filter(png_filter)
        if response == Gtk.ResponseType.OK:
            file_name = dialog.get_filename()
            dialog.destroy()
            if file_name.split(".")[-1] == "png":
                self.figure.savefig(file_name, transparent=True, dpi=None, format="png")
            elif file_name.split(".")[-1] == "svg":
                self.figure.savefig(file_name, transparent=True, dpi=None, format="svg")
            else:
                self.figure.savefig(file_name+".png", transparent=True, dpi=None, format="png")
                #TODO: Fix this!
#                selected_filter = dialog.get_filter()
#                if selected_filter is png_filter:
#                    self.figure.savefig(file_name+".png", transparent=True, dpi=None, format="png")
#                elif selected_filter is png_filter:
#                    self.figure.savefig(file_name+".png", transparent=True, dpi=None, format="png")
        else:
            dialog.destroy()

    def save_data_cb(self, action, parameters):
        dialog = Gtk.FileChooserDialog("Save simulation data", self, Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("Comma-separated values")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)

        dialog.set_current_name(self.hb.get_title()+" - "+self.simulation_output.analysis)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_name = dialog.get_filename()
            dialog.destroy()
            if file_name.split(".")[-1] != "csv":
                file_name += ".csv"
            self.simulation_output.save_csv(file_name)
        else:
            dialog.destroy()

    def close_cb(self, action, parameters):
        self.destroy()

    def insert_ac_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".ac dec nd fstart fstop")

    def insert_dc_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".dc srcnam vstart vstop vincr")

    def insert_tran_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".tran tstep tstop tstart")

    def insert_print_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".print ")

    def insert_model_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".model mname type (  )")

    def insert_lib_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".lib filename libname")

    def insert_include_cb(self, action, parameters):
        self.source_buffer.insert_at_cursor(".include filename")

    def _add_back_button(self):
        self.back_button = Gtk.Button()
        self.back_button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))

        self.back_button.connect("clicked", self.on_back_button_clicked)
        self.hb.pack_start(self.back_button)
        self.back_button.props.visible = False

    def _add_gear_button(self):
        self.gear_button = Gtk.MenuButton()

        #Set content
        icon = Gio.ThemedIcon(name="emblem-system-symbolic")
        # Use open-menu-symbolic on Gtk+>=3.14
        if Gtk.check_version(3, 14, 0) is None:
            icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        self.gear_button.add(image)

        # Use popover on Gtk+>=3.12
        if Gtk.check_version(3, 12, 0) is None:
            self.gear_button.set_use_popover(True)

        #Pack
        self.hb_rbox.pack_start(self.gear_button, False, False, 0)

    def _add_insert_button(self):
        self.insert_button = Gtk.MenuButton()

        #Set content
        icon = Gio.ThemedIcon(name="insert-text-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        self.insert_button.add(image)

        # Set menu model
        self.insert_button.props.menu_model = self.insertmenu

        # Use popover on Gtk+>=3.12
        if Gtk.check_version(3, 12, 0) is None:
            self.insert_button.set_use_popover(True)

        #Pack
        self.hb_rbox.pack_start(self.insert_button, False, False, 0)

    def _add_save_button(self):
        self.save_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-save-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        self.save_button.add(image)
        #self.save_button.get_style_context().add_class("image-buton")
        self.hb.pack_end(self.save_button)

    def _add_arrow_buttons(self):
        self.arrow_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(self.arrow_box.get_style_context(), "linked")

        self.back_button = Gtk.Button()
        self.back_button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        self.arrow_box.add(self.back_button)
        self.back_button.connect("clicked", self.on_back_button_clicked)

        self.forward_button = Gtk.Button()
        self.forward_button.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        self.arrow_box.add(self.forward_button)
        self.forward_button.connect("clicked", self.on_forward_button_clicked)

        self.hb.pack_start(self.arrow_box)

    def _add_load_button(self):
        self.load_button = Gtk.Button()
        self.load_button.set_label("Open")
#        icon = Gio.ThemedIcon(name="document-open-symbolic")
#        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
#        self.load_button.set_image(image)

        self.load_button.connect("clicked", self.on_button_open_clicked)
        self.hb.pack_start(self.load_button)

    def _add_simulate_button(self):
        self.simulate_button = Gtk.Button()
#        self.simulate_button.set_label("Simulate")
        icon = Gio.ThemedIcon(name="media-playback-start-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        self.simulate_button.add(image)

        self.simulate_button.connect("clicked", self.on_simulate_button_clicked)

        # Doesn't work on Gtk+>=3.12
        if Gtk.check_version(3, 12, 0) is not None:
            self.simulate_button.add_accelerator("clicked", Gtk.accel_groups_from_object(self)[0], Gdk.KEY_F5, 0, Gtk.AccelFlags.VISIBLE);

        self.simulate_button.props.sensitive = False
        self.hb_rbox.pack_start(self.simulate_button, False, False, 0)

    def _update_canvas(self, figure):
        self.simulation_box.remove(self.canvas)
        self.canvas = FigureCanvas(figure)  # a Gtk.DrawingArea
        self.simulation_box.pack_start(self.canvas, True, True, 0)
        self.canvas.show()

    def csd_are_supported(self):
        sessionType = os.environ.get('DESKTOP_SESSION')
        if sessionType == "gnome":
            return True
        # Other desktop environments doesn't play well with csd for now
        else:
            return False

    def set_error(self, title=None, message=None, message_type=Gtk.MessageType.ERROR, actions=None):
        '''set_error(self, title=None, message=None, message_type=Gtk.MessageType.ERROR, actions=None) -> None

        Sets and shows an information bar with actions as an option.

        params:
            actions -> (button_text, response_id, callback_function)
        '''
        if self.infobar is not None:
            self.infobar.close()
        self.infobar = InfoMessageBar()
        self.infobar.set_message_type(message_type)
        self.overview_box.pack_start(self.infobar, False, True, 0)

        if title is not None:
            self.infobar.message_title = title
        else:
            self.infobar.messsage_title = ""

        if message is not None:
            self.infobar.message_subtitle = message
        else:
            self.infobar.message_subtitle = ""

        if actions is not None:
            for action in actions:
                print action
                self.infobar.add_button(action[0], action[1]) #TODO: Fix self.infobar.add_button(action[0],action[1]) -> TypeError: Must be number, not str
                self.infobar.user_responses[action[1]] = action[2]

        self.infobar.show_all()

    def dismiss_error(self):
        if self.infobar is not None:
            self.infobar.props.visible = False
            self.infobar = None

    def simulation_view(self):
        self.stack.set_visible_child(self.simulation_box)
        self.back_button.props.sensitive = True
        self.forward_button.props.sensitive = False
        self.load_button.props.visible = False
        self.simulate_button.props.visible = False
        self.insert_button.props.visible = False
        self.gear_button.props.menu_model = self.gearmenu_simulation

    def overview_view(self):
        self.stack.set_visible_child(self.overview_box)
        self.back_button.props.sensitive = False
        self.forward_button.props.sensitive = True
        self.load_button.props.visible = True
        self.simulate_button.props.visible = True
        self.insert_button.props.visible = True
        self.gear_button.props.menu_model = self.gearmenu_overview

    def _on_destroy(self, data):
        self.destroy()

    def on_back_button_clicked(self, button):
        self.overview_view()

    def on_forward_button_clicked(self, button):
        self.simulation_view()

    def on_gear_button_clicked(self, button):
        self.figure.axes[0].legend(loc='lower left')

    def on_simulate_button_clicked(self, button):
        # Dismiss infobar messages (if they exists)
        self.dismiss_error()
        simulator = ngspice_simulation.Ngspice_async()
        dialog = running_dialog.RunningDialog(self,simulator.end_event)
        try:
            #First, save changes on disk
            self.on_save_button_clicked_overview(None)

            simulator.simulatefile(self.netlist_file_path)
            
            if dialog.run() == 1: # Not cancelled
                print simulator.result
                self.simulation_output = ngspice_simulation.NgspiceOutput.parse_file(self.netlist_file_path + ".out")
                self.figure = self.simulation_output.get_figure()
                self._update_canvas(self.figure)
                self.simulation_view()
            else:
                simulator.terminate()
                self.set_error(title="Simulation failed", message=simulator.error.message)            
        except Exception as e:
            self.set_error(title="Simulation failed", message=e.message)
        finally:
            dialog.destroy()

    def start_file_monitor(self):
        if self.schematic_file_path is not None:
            path = self.schematic_file_path
        elif self.netlist_file_path is not None:
            path = self.netlist_file_path
        else:
            return
        target_file = Gio.File.new_for_path(path)
        self.file_monitor = target_file.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.file_monitor.connect("changed", self.on_file_changed)

    def stop_file_monitor(self):
        if self.file_monitor is not None:
            self.file_monitor.cancel()

    def on_file_changed(self, file_monitor, _file, other_file, event_type):
        ''' on_file_changed(file_monitor,_file, other_file, event_type) -> None

        Callback function for file monitor on netlist file
        '''

        print file_monitor
        print _file
        print other_file
        print event_type

        if event_type == Gio.FileMonitorEvent.CHANGED or event_type == Gio.FileMonitorEvent.CREATED:
            self.set_error(title="Opened file changed on disk", message=None, message_type=Gtk.MessageType.WARNING, actions=[("Reload", 1000, self.on_infobar_reload_clicked)])

    def on_infobar_reload_clicked(self, button, response_id):
        if self.schematic_file_path is not None:
            self.load_file(self.schematic_file_path)
        elif self.netlist_file_path is not None:
            self.load_file(self.netlist_file_path)
        else:
            raise Exception("self.schematic_file_path and self.netlist_file_path are None")

    def load_file(self, path):
        '''
        load a file, converts it to netlist if needed and updates program state
        '''
        self.netlist_file_path = None
        self.schematic_file_path = None
        file_content = None
            #schematic to netlist conversion

        if os.path.splitext(path)[1] == ".sch":
            # Try convert schematic to netlist
            try:
                ngspice_simulation.Gnetlist.create_netlist_file(path, path + ".net")
                self.netlist_file_path = path + ".net"
                self.schematic_file_path = path
            except Exception as e:
                print e.message
                self.set_error(title="Schematic could not be converted to netlist", message=str(e.message))
                self.netlist_file_path = None
                self.schematic_file_path = None
                return
        else:
            self.netlist_file_path = path

        # Read netlist file
        if self.netlist_file_path is not None:
            with open(self.netlist_file_path) as f:
                file_content = f.read()

        # Set a file monitor
        self.start_file_monitor()

        if file_content is not None and self.netlist_file_path is not None:
            #Set window title
            netlist = ngspice_simulation.Netlist(file_content)
            title = netlist.get_title()
            if title is not None:
                self.hb.set_title(title)
            else:
                self.hb.set_title("")
            self.hb.set_subtitle(self.netlist_file_path)

            # Dismiss older errors
            self.dismiss_error()

            # Set content on source view
            self._open_state("opened")
            self.source_buffer.props.text = file_content
            self.simulate_button.props.sensitive = True
            self.canvas.show()

    def on_button_open_clicked(self, button):
        #Filechooserdialog initialization
        dialog = Gtk.FileChooserDialog("Please choose a file", self, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        netlist_filter = Gtk.FileFilter()
        netlist_filter.set_name("Netlist")
        netlist_filter.add_pattern("*.net")
        netlist_filter.add_pattern("*.cir")
        netlist_filter.add_pattern("*.ckt")
        dialog.add_filter(netlist_filter)

        gschem_filter = Gtk.FileFilter()
        gschem_filter.set_name("GEDA schematic")
        gschem_filter.add_mime_type("application/x-geda-schematic")
        dialog.add_filter(gschem_filter)

        dialog.set_filter(gschem_filter)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            try:
                path = dialog.get_filename()
                dialog.destroy()
                self.load_file(path)
            except Exception as e:
                self.set_error(title="File could not be loaded", message=str(e.message))
        else:
            dialog.destroy()

    def on_save_button_clicked_overview(self, button):
        self.stop_file_monitor()
        if not self.netlist_file_path:
            #TODO: Show a save file dialog
            pass
        with open(self.netlist_file_path, "w") as f:
            f.write(self.source_buffer.props.text)
        self.start_file_monitor()


class InfoMessageBar(Gtk.InfoBar):

    def __init__(self):
        Gtk.InfoBar.__init__(self)
        self.set_show_close_button(True)

        self.title_label = Gtk.Label(label="", use_markup=True, halign=Gtk.Align.START, justify=Gtk.Justification.LEFT, )
        self.subtitle_label = Gtk.Label(label="", use_markup=True, halign=Gtk.Align.START, justify=Gtk.Justification.LEFT, wrap=True)

        self.infobar_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.infobar_content_box.pack_start(self.title_label, False, False, 0)
        self.infobar_content_box.pack_start(self.subtitle_label, True, True, 0)
        self.get_content_area().add(self.infobar_content_box)

        self.user_responses = {} # {response_id: callback_function, ...}

        self.connect("response", self._on_infobar_close_clicked)

    @property
    def message_title(self):
        return self.title_label.props.label

    @message_title.setter
    def message_title(self, value):
        self.title_label.props.label = "<b>" + value + "</b>"

    @property
    def message_subtitle(self):
        return self.subtitle_label.props.label

    @message_subtitle.setter
    def message_subtitle(self, value):
        self.subtitle_label.props.label = "<small>" + value + "</small>"

    def _on_infobar_close_clicked(self, button, response_id):
        if response_id == int(Gtk.ResponseType.CLOSE):
            self.props.visible = False
        else:
            self.user_responses[response_id](button, response_id)
            self.props.visible = False


class TransientSimulationWindow(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Transient Simulation", parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

#        self.set_border_width(10)
#        self.resize(800, 800)
        self.set_default_size(900, 600)
        self.props.resizable = False
#        self.hb = Gtk.HeaderBar()
#        self.hb.props.show_close_button = False
#        self.hb.props.title = "Transient Simulation"
#        self.set_titlebar(self.hb)
#
#        self.cancel_button = Gtk.Button("Cancel")
#        self.cancel_button.connect("clicked", self.on_cancel_button_clicked)
#        self.simulate_button = Gtk.Button("Simulate")
#        self.simulate_button.connect("clicked", self.on_simulate_button_clicked)

#        self.hb.pack_start(self.cancel_button)
#        self.hb.pack_end(self.simulate_button)

        # main box
        hbox = Gtk.Box(spacing=6)
        self.get_content_area().add(hbox)
        self.get_content_area().set_border_width(6)
        #Parameter box
        sbox = Gtk.Box(spacing=6)
        hbox.pack_end(sbox, False, False, 0)

        # simulation parameters
        grid = Gtk.Grid(row_spacing=6, column_spacing=6)

        label_start = Gtk.Label("Start time")
        label_start.props.xalign = 1
        label_end = Gtk.Label("End time")
        label_end.props.xalign = 1
        label_interval = Gtk.Label("Sample interval")
        label_interval.props.xalign = 1
        entry_start = Gtk.Entry()
        entry_start.set_hexpand(True)
        entry_end = Gtk.Entry()
        entry_end.set_hexpand(True)
        entry_interval = Gtk.Entry()
        entry_interval.set_hexpand(True)

        grid.attach(label_start, 0, 0, 1, 1)
        grid.attach(label_end, 0, 1, 1, 1)
        grid.attach(label_interval, 0, 2, 1, 1)
        grid.attach_next_to(entry_start, label_start, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(entry_end, label_end, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(entry_interval, label_interval, Gtk.PositionType.RIGHT, 1, 1)

        hbox.pack_start(grid, True, True, 1)

        # Nodes listbox
        scrolled = Gtk.ScrolledWindow(None, None)
#        scrolled.set_hexpand(True);
#        scrolled.set_hexpand(True)
#        scrolled.set_vexpand(True)
#        scrolled.props.expand = True

        listbox = Gtk.ListBox()
        listbox.props.expand = True
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        scrolled.add(listbox)

        hbox.pack_start(scrolled, False, True, 0)

        for i in range(4):
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.add(hbox)
            check = Gtk.CheckButton()
            label = Gtk.Label("V"+str(i), xalign=0)
            hbox.pack_start(check, False, True, 0)
            hbox.pack_start(label, True, True, 0)

            listbox.add(row)

        self.show_all()

    def on_cancel_button_clicked(self, button):
        self.response(Gtk.ResponseType.CANCEL)

    def on_simulate_button_clicked(self, button):
        self.response(Gtk.ResponseType.OK)

if __name__ == '__main__':
    win = MainWindow()
    win.connect("delete-event", Gtk.main_quit)

    win.show_all()
    Gtk.main()
