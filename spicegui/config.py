#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SpiceGUI constants and option functions."""

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

import os


APPLICATION_ID = "org.rafael1193.spicegui"
DOMAIN = "spicegui"
GSETTINGS_BASE_KEY = "org.rafael1193.spicegui"
HELP_URL = "https://github.com/rafael1193/spicegui/wiki"
PROGRAM_NAME = "SpiceGUI"
PROGRAM_NAME_LOWER = PROGRAM_NAME.lower()
VERSION = "0.3"
PROGRAM_WEBSITE = "https://rafael1193.github.io/spicegui/"


def csd_are_supported():
    sessionType = os.environ.get('DESKTOP_SESSION')
    if sessionType == "gnome":
        return True
    # Other desktop environments doesn't play well with csd for now
    else:
        return False

