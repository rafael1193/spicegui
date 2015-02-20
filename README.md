SpiceGUI
=======

[![Join the chat at https://gitter.im/rafael1193/spicegui](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/rafael1193/spicegui?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**SpiceGUI** is a program that aims to make circuit simulation on GNU/Linux operating systems easier with a modern and easy to use graphical user interface. This program makes more straightforward the process from schematic edition to result analysis with a modern Gtk3 interface.

Installing
---------

### Fedora

Get it from [rafael1193/SpiceGUI fedora copr repository](http://copr.fedoraproject.org/coprs/rafael1193/SpiceGUI/)

Run

    $ sudo dnf install dnf-plugins-core
    $ sudo dnf copr enable rafael1193/SpiceGUI
    $ sudo dnf install spicegui

Or

    $ cd /etc/yum.repos.d/
    $ sudo wget http://copr.fedoraproject.org/coprs/rafael1193/SpiceGUI/repo/fedora-21/rafael1193-SpiceGUI-fedora-21.repo
    $ sudo yum install spicegui

### Others

Download release tarball and run

    $ python setup.py build
    $ sudo python setup.py install

