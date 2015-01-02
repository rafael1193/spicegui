#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SpiceGUI main script."""

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

import os
import os.path

import config


def get_locale_path():
    """Get locale folder path.
    
    Returns:
        locale_path: Locale folder path.
        
    Raises:
        IOError: If locale path cannot be found.
    """
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)),"locale")
    installed_base = os.path.join(" ",*(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[:-4])).lstrip(" ")  # Remove lib/python2.7/site-packages/spicegui
    installed_ext = os.path.join("share", "locale")
    installed = os.path.join(installed_base, installed_ext)

    if os.path.exists(local):
        return local
    elif os.path.exists(installed):
        return installed
    else:
        raise IOError("Locale path not found.")

def start():
    """Starts SpiceGUI application."""
    import gettext
    import locale

    domain = config.DOMAIN
    locale_path = get_locale_path()

    gettext.install(domain, locale_path)
    locale.textdomain(domain)
    locale.bindtextdomain(domain, locale_path)
    locale.textdomain(domain)
    locale.setlocale(locale.LC_ALL, '')

    import application
    import sys
    app = application.SpiceGUI()
    app.run(sys.argv)

if __name__ == "__main__":
    start()
