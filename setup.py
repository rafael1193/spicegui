#!/usr/bin/env python
#-*-coding:utf-8-*-

"""Setup for SpiceGUI
"""

from setuptools import setup, find_packages

import subprocess

import spicegui.config

__prj__ = spicegui.config.PROGRAM_NAME_LOWER
__author__ = "Rafael Bailón-Ruiz"
__mail__ = "rafaelbailon at ieee dot org"
__url__ = spicegui.config.PROGRAM_WEBSITE
__source__ = spicegui.config.PROGRAM_WEBSITE
__version__ = spicegui.config.VERSION
__license__ = "GPL3"

dependencies = []

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
    
    "data_files":[('/usr/share/applications/', ['spicegui/data/SpiceGUI.desktop']),
                  ('/usr/share/glib-2.0/schemas/', ['spicegui/data/org.rafael1193.spicegui.gschema.xml']),
                  ('/usr/share/gtksourceview-3.0/language-specs/', ['spicegui/data/spice-netlist.lang']),
                  ('/usr/share/icons/hicolor/scalable/apps/', ['spicegui/data/spicegui.svg']),
                  ('/usr/share/appdata/',['spicegui/data/SpiceGUI.appdata.xml']),
                  ('/usr/share/locale/es/LC_MESSAGES/',['spicegui/locale/es/LC_MESSAGES/spicegui.mo'])],

    #auto create scripts
    "entry_points": {
        'console_scripts': [
            'spicegui = spicegui:start',
        ],
        'gui_scripts': [
            'spicegui = spicegui:start',
        ]
    }
}

def update_icon_cache():
    try:
        subprocess.call(["gtk-update-icon-cache", "/usr/share/icons/hicolor"])
    except Exception: 
        pass
    
def glib_compile_schemas():
    try:
        subprocess.call(["glib-compile-schemas", "/usr/share/glib-2.0/schemas/"])
    except Exception:
        pass

def compile_message_catalog():
    try:
        subprocess.call(["msgfmt", "-o", "spicegui/locale/es/LC_MESSAGES/spicegui.mo", "spicegui/locale/es/LC_MESSAGES/spicegui.po"])
    except Exception:
        pass

compile_message_catalog()

setup(**params)

update_icon_cache()
glib_compile_schemas()


