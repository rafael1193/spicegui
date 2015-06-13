[![Join the chat at https://gitter.im/rafael1193/spicegui](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/rafael1193/spicegui?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

SpiceGUI
=======

**SpiceGUI** is a program that aims to make circuit simulation on GNU/Linux operating systems easier with a modern and easy to use graphical user interface. This program makes more straightforward the process from schematic edition to result analysis with a modern Gtk3 interface.

Installation
------------

### Ubuntu / Linux Mint / elementaryOS

Add [ppa:rafael1193/spicegui](https://launchpad.net/~rafael1193/+archive/ubuntu/spicegui) repository.

    $ sudo add-apt-repository ppa:rafael1193/spicegui
    $ sudo apt-get update
    $ sudo apt-get install spicegui

### Fedora

Add [rafael1193/SpiceGUI](http://copr.fedoraproject.org/coprs/rafael1193/SpiceGUI/) repository.

    $ sudo dnf copr enable rafael1193/SpiceGUI
    $ sudo dnf install spicegui

### Others

Download release tarball and run

    $ python setup.py build
    $ sudo python setup.py install

