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
import sys
import ConfigParser

from qdailies.lib import config
from qdailies.lib.logger import log

class Prefs(ConfigParser.SafeConfigParser):

    def __init__(self, prefs=None, read_only=True):
        ConfigParser.SafeConfigParser.__init__(self)
        if prefs is None:
            prefs = os.path.join(config.HOMEDIR, '.qdailies.ini')
        self.prefs = prefs
        self._read_only = read_only
        self.readfp(open(os.path.join(config.PREFS_ROOT, 'defaults.ini')))
        self.read(self.prefs)

    def write(self):
        if self._read_only:
            log.warning('Attempt to write out prefs file when marked read-only!')
        else:
            f = open(self.prefs, 'w')
            ConfigParser.SafeConfigParser.write(self, f)
            f.close()

    def get(self, section, option, default='', raw=False, vars=None):
        ''' fetch an option if it exists, otherwise return the default.
        if there is no section as named it will return None.

        @param: section
        @type:  string
        @param: option
        @type:  string
        @param: raw
        @type:  bool
        @param: vars
        @type:  list
        @param: default
        @type:  string    
        '''
        option = option.lower()
        retValue = default
        if section in self.sections():
            if option in self.options(section):
                retValue = ConfigParser.SafeConfigParser.get(self, section=section, option=option, raw=raw, vars=vars)
        else:
            retValue = None
        return retValue
