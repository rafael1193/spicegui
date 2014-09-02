#!/usr/bin/env python
#-*-coding:utf-8-*-

"""Setup for SpiceGUI
"""

import sys
from setuptools import setup, find_packages

__prj__ = "SpiceGUI"
__author__ = "Rafael Bailón-Ruiz"
__mail__ = "rafaelbailon at ieee dot org"
__url__ = ""
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
    "package_data": {'': ['*.png', '*.gif', '*.jpg', '*.json', '*.qss',
        '*.js', '*.html', '*.css', '*.qm', '*.qml']},

    # include ninja pkg and setup the run script
    "packages": find_packages(),

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

setup(**params)

