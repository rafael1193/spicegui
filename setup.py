#!/usr/bin/env python
#-*-coding:utf-8-*-

"""Setup for SpiceGUI
"""

from setuptools import setup, find_packages

import subprocess

__prj__ = "spicegui"
__author__ = "Rafael Bailón-Ruiz"
__mail__ = "rafaelbailon at ieee dot org"
__url__ = "https://github.com/rafael1193/spicegui"
__source__ = "https://github.com/rafael1193/spicegui"
__version__ = "0.1"
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
               "Programming Language :: Python :: 2"],

    "install_requires": dependencies,

    # include all resources
    "include_package_data": True,
    "package_data": {'spicegui': ['data/*.glade']},

    "packages": find_packages(),
    
    "data_files":[('/usr/share/applications/', ['spicegui/data/SpiceGUI.desktop']),
                  ('/usr/share/glib-2.0/schemas/', ['spicegui/data/org.rafael1193.spicegui.gschema.xml']),
                  ('/usr/share/gtksourceview-3.0/', ['spicegui/data/spice-netlist.lang']),
                  ('/usr/share/icons/hicolor/scalable/apps/', ['spicegui/data/spicegui.svg'])],

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
    subprocess.call(["gtk-update-icon-cache","/usr/share/icons/hicolor"])

setup(**params)

update_icon_cache()


