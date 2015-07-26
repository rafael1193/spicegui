#!/usr/bin/env python3
# -*-coding:utf-8-*-

"""Setup for SpiceGUI"""

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


from __future__ import print_function

from setuptools import find_packages

from distutils.core import setup
from distutils.command.install_data import install_data

import subprocess
import sys

import spicegui.config

__prj__ = spicegui.config.PROGRAM_NAME_LOWER
__author__ = "Rafael Bailón-Ruiz"
__mail__ = "rafaelbailon at ieee dot org"
__url__ = spicegui.config.PROGRAM_WEBSITE
__source__ = spicegui.config.PROGRAM_WEBSITE
__version__ = spicegui.config.VERSION
__license__ = "GPL3"

dependencies = []


class MyInstallData(install_data):

    def update_icon_cache(self):
        try:
            root = self.root if self.root is not None else ''
            subprocess.call(['gtk-update-icon-cache', root + '/usr/share/icons/hicolor'])
        except:
            print("ERROR: unable to update icon cache", file=sys.stderr)

    @classmethod
    def update_desktop_database(cls):
        try:
            subprocess.call(['update-desktop-database'])
        except:
            print("ERROR: unable to update desktop database", file=sys.stderr)

    def glib_compile_schemas(self):
        try:
            root = self.root if self.root is not None else ''
            subprocess.call(['glib-compile-schemas', root + '/usr/share/glib-2.0/schemas/'])
        except:
            print("ERROR: unable to compile GSettings schemas", file=sys.stderr)

    @classmethod
    def compile_message_catalog(cls):
        try:
            subprocess.call(['msgfmt', '-o', 'spicegui/locale/es/LC_MESSAGES/spicegui.mo',
                             'spicegui/locale/es/LC_MESSAGES/spicegui.po'])
        except:
            print("ERROR: unable to compile \"es\" message catalog", file=sys.stderr)

    def run(self):
        if sys.platform.startswith('linux'):
            self.compile_message_catalog()
        install_data.run(self)
        if sys.platform.startswith('linux'):
            self.update_desktop_database()
            self.update_icon_cache()
            self.glib_compile_schemas()


CMDCLASS = {'install_data': MyInstallData}

params = {
    "name": __prj__,
    "version": __version__,
    "description": __doc__,
    "author": __author__,
    "author_email": __mail__,
    "url": __url__,
    "license": __license__,
    "keywords": "spice gui circuit simulator",
    "classifiers": ["Development Status :: Development Status :: 4 - Beta",
                    "Topic :: Engineering",
                    "License :: OSI Approved :: GNU General Public License (GPL)",
                    "Natural Language :: English",
                    "Operating System :: OS Independent",
                    "Programming Language :: Python :: 2",
                    "Programming Language :: Python :: 3"],

    "install_requires": dependencies,

    # include all resources
    "include_package_data": True,
    "package_data": {'spicegui': ['data/*.glade', 'data/*.ui']},

    "packages": find_packages(),

    "data_files": [('/usr/share/applications/', ['spicegui/data/SpiceGUI.desktop']),
                   ('/usr/share/glib-2.0/schemas/', ['spicegui/data/org.rafael1193.spicegui.gschema.xml']),
                   ('/usr/share/gtksourceview-3.0/language-specs/', ['spicegui/data/spice-netlist.lang']),
                   ('/usr/share/icons/hicolor/scalable/apps/', ['spicegui/data/spicegui.svg']),
                   ('/usr/share/icons/hicolor/symbolic/apps/', ['spicegui/data/spicegui-symbolic.svg']),
                   ('/usr/share/appdata/', ['spicegui/data/SpiceGUI.appdata.xml']),
                   ('/usr/share/locale/es/LC_MESSAGES/', ['spicegui/locale/es/LC_MESSAGES/spicegui.mo'])],

    # auto create scripts
    "entry_points": {
        'console_scripts': [
            'spicegui = spicegui:start',
        ],
        'gui_scripts': [
            'spicegui = spicegui:start',
        ]
    },

    'cmdclass': {'install_data': MyInstallData}
}

setup(**params)
