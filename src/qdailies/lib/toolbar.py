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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic

from qdailies.lib import config
from qdailies.lib import style

class ToolBar(QtGui.QToolBar):

    def __init__(self, title, parent):
        super(ToolBar, self).__init__(parent)
        self.setObjectName('toolbar-'+title.replace(' ', ''))
        self.setFloatable(False)
        self.setMovable(False)
        self.setStyleSheet(style.toolbar)
