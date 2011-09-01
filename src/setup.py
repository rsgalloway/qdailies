#!/bin/env/python

##########################################################################
#
# Copyright 2011-2012 Enluminari Incorporated.
#
# NOTICE:  All information contained herein is, and remains
# the property of Enluminari Incorporated and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to Enluminari Incorporated
# and its suppliers and may be covered by U.S. and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Enluminari Incorporated.
#
##########################################################################

import os
from setuptools import setup

def get_packages(path):
    packages = []
    for (path, dirs, files) in os.walk(path):
        packages.append(path)
    return packages

setup(
    name='qdailies',
    author='Ryan Galloway',
    author_email='ryan@enluminari.com',
    version='0.1',
    description='QDailies is a simple vfx/animation dailies tool built for use with shotgun and rv',
    url='http://www.github.com/enluminari/qdailies',
    license='',
    keywords = "visual effects vfx python animation digital studio production dailies",
    platforms=['OS Independent'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
    ],
    packages=get_packages('qdailies'),
    scripts=['bin/q', 'bin/newq'],
    package_data = {
        '': ['*.py', '*.ui', '*.ini', '*.html', '*.css', '*.js', '*.png', '*.gif', '*.ico'],
    }
)
