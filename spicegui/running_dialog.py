# -*- coding: utf-8 -*-

from gi.repository import Gtk, GObject

class RunningDialog(Gtk.Dialog):

    def __init__(self, parent, event):
        Gtk.Dialog.__init__(self, "Simulation", parent, Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT|Gtk.DialogFlags.USE_HEADER_BAR,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        self.event = event
        
        self.set_default_size(150, 100)
        self.set_default_response(Gtk.ResponseType.CANCEL)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.activity_mode = True
        self.progress_bar.pulse()
        self.progress_bar.set_text("Running simulation")
        self.progress_bar.set_show_text(True)
        
        self.label = Gtk.Label(label="Running simulation")
        self.label.set_vexpand(True)
        
        self.spinner = Gtk.Spinner()
        self.spinner.start()
        self.spinner.set_vexpand(True)
        
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox.pack_start(self.spinner, True, True, 18)
        self.hbox.pack_start(self.label, True, True, 18)
        
        
        box = self.get_content_area()
        box.add(self.hbox)
        
        self.timeout_id = GObject.timeout_add(50, self.on_timeout, None)
        
        self.show_all()
        
    def on_timeout(self, user_data):
        """
        Update value on the progress bar
        """
        self.progress_bar.pulse()
        if self.event.is_set(): # if thread finished
            self.response(1) # 1 is an application-defined response type
        return True


if __name__ == "__main__":
    win = Gtk.Window()
    dialog = RunningDialog(win)
    dialog.run()
    dialog.destroy()
    win.destroy()


