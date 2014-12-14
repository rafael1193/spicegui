# -*- coding: utf-8 -*-

from __future__ import print_function

from gi.repository import Gtk, GObject


class RunningDialog(Gtk.Dialog):

    def __init__(self, parent, event):
        if Gtk.check_version(3, 12, 0) is None: # Use header bar
            Gtk.Dialog.__init__(self, "Simulation", parent, 
                                Gtk.DialogFlags.MODAL | 
                                Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL), 
                                use_header_bar=True)
            self.get_header_bar().set_show_close_button(False)
        else: # Do not use header bar
            Gtk.Dialog.__init__(self, "Simulation", parent, 
                    Gtk.DialogFlags.MODAL | 
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        
        self.event = event
        
        self.set_default_size(150, 100)
        self.props.resizable = False 
        self.set_default_response(Gtk.ResponseType.CANCEL)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.activity_mode = True
        self.progress_bar.pulse()
        self.progress_bar.set_text(u"Running ngspice…")
        self.progress_bar.set_show_text(True)
        
#        self.label = Gtk.Label(label=u"Running ngspice…")
#        self.label.set_vexpand(True)
        
#        self.spinner = Gtk.Spinner()
#        self.spinner.start()
#        self.spinner.set_vexpand(True)
        
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.hbox.set_margin_left(18)
        self.hbox.set_margin_top(18)
        self.hbox.set_margin_bottom(18)
        self.hbox.set_margin_right(18)
        self.hbox.set_vexpand(True)
        self.hbox.set_spacing(12)
        
        self.hbox.pack_start(self.progress_bar, True, True, 18)
#        self.hbox.pack_start(self.spinner, True, True, 18)
#        self.hbox.pack_start(self.label, True, True, 18)
        
        
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
    from multiprocessing import Event
    event_test = Event()
    win = Gtk.Window()
    dialog = RunningDialog(win, event_test)
    dialog.run()
    dialog.destroy()
    win.destroy()


