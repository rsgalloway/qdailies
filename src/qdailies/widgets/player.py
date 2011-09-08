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

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic
from PyQt4.phonon import Phonon

from qdailies.lib import config
from qdailies.lib.logger import log

class Player(Phonon.VideoPlayer):

    def __init__(self, parent=None, main=None):
        super(Player, self).__init__(Phonon.VideoCategory, parent)
        self.setObjectName('player')
        self.main = main
        self.setFullScreen(False)

        self.mediaObject().setTickInterval(10)
        self.connect(self.main, QtCore.SIGNAL('load (PyQt_PyObject)'), self.handleLoad)
        self.connect(self.main, QtCore.SIGNAL('play ()'), self.handlePlay)
        self.connect(self.main, QtCore.SIGNAL('pause ()'), self.handlePause)
        self.connect(self, QtCore.SIGNAL('finished ()'), self.handleFinished)

        self.version = None

    def keyPressEvent(self, event):
        return self.main.keyPressEvent(event)

    def handleLoad(self, version):
        log.debug('handleLoad: %s' % version.left)
        self.version = version
        if not version.left or not os.path.isfile(version.left):
            log.info('File not found: %s' % version.left)
            self.stop()
        self.load(Phonon.MediaSource(version.left))
        self.main.emit(QtCore.SIGNAL('totalTime (PyQt_PyObject)'), self.totalTime())

    def handlePlay(self):
        self.play()

    def handlePause(self):
        self.pause()

    def isFullScreen(self):
        return self.__fullscreen

    def setFullScreen(self, fullscreen):
        self.__fullscreen = fullscreen
        self.videoWidget().setFullScreen(fullscreen)

    def handleFinished(self):
        self.main.emit(QtCore.SIGNAL('finished (PyQt_PyObject)'), self.version)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Player()
    win.show()
    win.raise_()
    sys.exit(app.exec_())
