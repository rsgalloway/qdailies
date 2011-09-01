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

class Dock(QtGui.QDockWidget):
    '''
    Subclass of QDockWidget. Used as a container for the widgets.
    '''
    def __init__(self, title, parent):
        super(Dock, self).__init__(parent)
        self.setObjectName('dock-'+title.replace(' ', ''))
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFeatures(QtGui.QDockWidget.DockWidgetMovable)
        self.setStyleSheet(style.dock)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def closeEvent(self, event):
        if hasattr(self.parent(), 'removeDock'):
            self.parent().removeDock(str(self.name))
        self.widget().close()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space and False:
            self.parent().toggleMaximizedDock(self)
        else:
            QtGui.QDockWidget.keyPressEvent(self, event)
