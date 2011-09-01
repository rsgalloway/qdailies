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
import Queue
import traceback

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from qdailies.lib import config
from qdailies.lib import style
from qdailies.lib.logger import log
from qdailies.lib.threads import ShotgunShowsThread, ShotgunShotsThread

class SearchBar(QtGui.QWidget):

    def __init__(self, parent=None, dock=None):
        super(SearchBar, self).__init__(parent)
        self.dock = dock
        uic.loadUi(os.path.join(config.UI_ROOT, 'search.ui'), self)

        self.setObjectName('searchBar')
        self.setStyle(QtGui.QStyleFactory.create('cleanlooks'))
        self.setStyleSheet(style.searchbar)

        self.shows = {}
        self.shots = {}

        self.connect(self.showCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeShow)
        self.connect(self.parent(), QtCore.SIGNAL('changeShow (PyQt_PyObject)'), self.handleChangeShow)
        self.connect(self.editSearch, QtCore.SIGNAL('returnPressed ()'), self.handleFind)
        self.connect(self.btnNew, QtCore.SIGNAL('pressed ()'), self.handleNew)

        self.threads_queue = Queue.Queue()
        self.getShows()

    def updateCompleter(self, shots):
        self.shots = {}
        for shot in shots:
            self.shots[str(shot.get('code'))] = shot
        self.completer = QtGui.QCompleter(self.shots.keys())
        self.completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.editSearch.setCompleter(self.completer)

    def getShows(self):
        self._showsThread = ShotgunShowsThread(self)
        self.connect(self._showsThread, QtCore.SIGNAL("shows (PyQt_PyObject)"), self.handleShows)
        self.connect(self._showsThread, QtCore.SIGNAL("error (PyQt_PyObject)"), self.handleShowsError)
        self._showsThread.start()
        self.threads_queue.put(self._showsThread)

    def getShots(self, show):
        log.debug('find shots: %s' % show)
        self._shotsThread = ShotgunShotsThread(self, self.shows.get(show))
        self.connect(self._shotsThread, QtCore.SIGNAL("shots (PyQt_PyObject)"), self.updateCompleter)
        self.connect(self._shotsThread, QtCore.SIGNAL("error (PyQt_PyObject)"), self.handleShotsError)
        self._shotsThread.start()
        self.threads_queue.put(self._shotsThread)

    def handleShows(self, shows):
        self.shows = {}
        self.showCombo.clear()
        for show in shows:
            self.shows[str(show.get('name'))] = show
            self.showCombo.addItem(show.get('name'))

    def handleShowsError(self, error):
        self.parent().parent().info(error)

    def handleShotsError(self, error):
        self.parent().parent().info(error)

    def handleChangeShow(self, show=None):
        if show is None:
            show = str(self.showCombo.currentText().toAscii())
        if not show:
            return
        idx = self.showCombo.findText(show)
        if idx >=0 and idx != self.showCombo.currentIndex():
            self.showCombo.setCurrentIndex(idx)
        self.getShots(str(show))

    def handleFind(self, show=None, shot=None, task=None):
        log.debug('find %s %s %s' %(show, shot, task))
        if show is None:
            show = str(self.showCombo.currentText().toAscii())
        if shot is None:
            shot = str(self.editSearch.text().toAscii())
        log.debug('find versions: %s' % shot)
        if not shot:
            self.parent().parent().emit(QtCore.SIGNAL('showQueue ()'), )
        else:
            self.parent().parent().emit(QtCore.SIGNAL('findVersions (PyQt_PyObject)'), self.shots.get(shot))

    def handleNew(self):
        from widgets.new import NewVersionWidget
        win = NewVersionWidget()
        win.getShows()
        win.exec_()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Deck()
    win.show()
    win.raise_()
    sys.exit(app.exec_())

