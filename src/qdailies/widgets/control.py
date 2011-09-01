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
import traceback

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from qdailies.lib import config
from qdailies.lib import style

class ControlBar(QtGui.QWidget):

    def __init__(self, parent=None, main=None, player=None):
        super(ControlBar, self).__init__(parent)
        uic.loadUi(os.path.join(config.UI_ROOT, 'deck.ui'), self)
        self.main = main
        self.player = player
        self.setObjectName('controlbar')
        self.setStyle(QtGui.QStyleFactory.create('cleanlooks'))
        self.setStyleSheet(style.controlbar)

        self.seekSlider.setMediaObject(self.player.mediaObject())

        self.connect(self.btnPlay, QtCore.SIGNAL('pressed ()'), self.handlePlay)

        if not self.player:
            self.btnPlay.setDisabled(True)
            self.btnPrev.setDisabled(True)
            self.btnNext.setDisabled(True)

    def handlePlay(self):
        if self.player.isPlaying():
            self.main.emit(QtCore.SIGNAL('pause ()'))
            self.btnPlay.setStyleSheet('background-image: url(%s/icon.btn.play.png)' % config.GFX_ROOT)
        else:
            self.main.emit(QtCore.SIGNAL('play ()'))
            if self.player.isPlaying():
                self.btnPlay.setStyleSheet('background-image: url(%s/icon.btn.pause.png)' % config.GFX_ROOT)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = ControlBar()
    win.show()
    win.raise_()
    sys.exit(app.exec_())

