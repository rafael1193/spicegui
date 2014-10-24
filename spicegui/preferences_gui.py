from gi.repository import Gio, Gtk

class Preferences(object):
    GSETTINGS_BASE_KEY = "org.rafael1193.spicegui"
    def __init__(self, parent):
       
        # Get window
        self.builder = Gtk.Builder()
        try:
            self.builder.add_from_file("data/preferences.glade")
        except:
            self.builder.add_from_file("/usr/share/spicegui/data/preferences.glade")

        window = self.builder.get_object('preferences_window')
        window.set_transient_for(parent)
        
        # Get gsettings reference
        settings = Gio.Settings.new(self.GSETTINGS_BASE_KEY)
        
        show_legend_checkbutton = self.builder.get_object('show_legend_checkbutton')
        show_legend_checkbutton.set_active(settings.get_boolean("show-legend"))
        # If setting is changed externally
        settings.connect("changed::show-legend", self.on_show_legend_setting_changed, show_legend_checkbutton)
        # If checkbox is toggled
        show_legend_checkbutton.connect('toggled', self.on_show_legend_checkbutton_toggled, settings)
        
        legend_position_comboboxtext = self.builder.get_object('legend_position_comboboxtext')
        legend_position_comboboxtext.set_active_id(settings.get_string("legend-position"))
        # If setting is changed externally
        settings.connect("changed::legend-position", self.on_legend_position_setting_changed, legend_position_comboboxtext)
        # If combox item is selected
        legend_position_comboboxtext.connect('changed', self.on_legend_position_comboboxtext_changed, settings)
        
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
                                  
    def on_window_destroy(self, widget, data=None):
        Gtk.main_quit()

if __name__ == "__main__":
    app = App() 
