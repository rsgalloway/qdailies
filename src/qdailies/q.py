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
import tempfile

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from qdailies.lib import config
from qdailies.lib import style
from qdailies.lib.prefs import Prefs
from qdailies.lib.dock import Dock
from qdailies.lib.toolbar import ToolBar
from qdailies.lib.threads import *
from qdailies.lib.fetch_image import URLImage
from qdailies.widgets.control import ControlBar
from qdailies.widgets.search import SearchBar
from qdailies.widgets.tree import Tree
from qdailies.widgets.player import Player

class QDailies(QtGui.QMainWindow):
    DOCKS = dict()
    TOOLBARS = dict()
    WIDGETS = dict()
    SIGS = dict()

    def __init__(self, **kwargs):
        QtGui.QMainWindow.__init__(self)
        uic.loadUi(os.path.join(config.UI_ROOT, 'main.ui'), self)
        self.setWindowState(QtCore.Qt.WindowActive)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle('Q')
        self.setWindowIcon(QtGui.QIcon(os.path.join(config.GFX_ROOT, 'icon.logo.main.bg.png')))
        self.setStyle(QtGui.QStyleFactory.create('cleanlooks'))

        self.setDockNestingEnabled(True)
        self.centralWidget().hide()
        self.statusBar().hide()

        self.prefs = Prefs(read_only=False)

        # TODO: pass in widget to dock & toolbar init
        self.WIDGETS['tree'] = Tree(self, main=self)
        self.WIDGETS['player'] = Player(self, main=self)
        self.WIDGETS['controlbar'] = ControlBar(self, main=self, player=self.WIDGETS['player'])
        self.WIDGETS['searchbar'] = SearchBar(self)

        self.TOOLBARS['controlbar'] = ToolBar('controlbar', self)
        self.TOOLBARS['searchbar'] = ToolBar('searchbar', self)
        self.TOOLBARS['controlbar'].addWidget(self.WIDGETS['controlbar'])
        self.TOOLBARS['searchbar'].addWidget(self.WIDGETS['searchbar'])

        self.DOCKS['tree'] = Dock('tree', self)
        self.DOCKS['tree'].setWidget(self.WIDGETS['tree'])
        self.DOCKS['player'] = Dock('player', self)
        self.DOCKS['player'].setWidget(self.WIDGETS['player'])

        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.TOOLBARS['controlbar'])
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.TOOLBARS['searchbar'])
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.DOCKS['tree'])
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.DOCKS['player'])

        self.setStyleSheet(style.main)

        self.settings = QtCore.QSettings('Enluminari', 'QDailies');
        self.restoreGeometry(self.settings.value('geometry').toByteArray());
        self.restoreState(self.settings.value('windowState').toByteArray());

        project = kwargs.get('project', None)
        if project:
            self.emit(QtCore.SIGNAL('changeShow (PyQt_PyObject)'), project)

        self.connect(self.WIDGETS['tree'], QtCore.SIGNAL('versionAddedtoQueue (PyQt_PyObject)'), self.handleVersionAdded)
        self.connect(self.WIDGETS['tree'], QtCore.SIGNAL('versionRemovedFromQueue (PyQt_PyObject)'), self.handleVersionRemoved)

        menu = QtGui.QMenu('Window', self)
        menu.addAction('Fullscreen', self.toggleFS, QtGui.QKeySequence(QtCore.Qt.ControlModifier + QtCore.Qt.Key_F))
        menu.addSeparator()
        menu.addAction('Play', self.togglePlay, QtGui.QKeySequence(QtCore.Qt.ControlModifier + QtCore.Qt.Key_P))
        menu.addAction('Next', self.toggleNext, QtGui.QKeySequence(QtCore.Qt.AltModifier + QtCore.Qt.Key_N))
        menu.addAction('Previous', self.togglePrev, QtGui.QKeySequence(QtCore.Qt.AltModifier + QtCore.Qt.Key_P))

        self.menuBar().addMenu(menu)

    def info(self, msg="Error", title="Error"):
        log.debug(msg)
        dialog = QtGui.QMessageBox()
        dialog.information(self, title, msg)

    def handleVersionAdded(self, version):
        self.DOCKS['tree'].setWindowTitle('%d items queued' % len(self.WIDGETS['tree'].queue()))

    def handleVersionRemoved(self, version):
        l = len(self.WIDGETS['tree'].queue())
        if l == 0:
            self.DOCKS['tree'].setWindowTitle('')
        else:
            self.DOCKS['tree'].setWindowTitle('%d items queued' % l)

    def toggleFS(self):
        player = self.WIDGETS['player']
        player.setFullScreen(not player.isFullScreen())

    def togglePlay(self):
        control = self.WIDGETS['controlbar']
        control.handlePlay()

    def toggleNext(self):
        tree = self.WIDGETS['tree']
        tree.handleNext()

    def togglePrev(self):
        tree = self.WIDGETS['tree']
        tree.handlePrev()

    def toggleUp(self):
        tree = self.WIDGETS['tree']
        tree.versionsTree.selectPrev()

    def toggleDown(self):
        tree = self.WIDGETS['tree']
        tree.versionsTree.selectNext()

    def keyPressEvent(self, event):
        key = event.key()

        # toggle playback
        if key == QtCore.Qt.Key_Space:
            self.togglePlay()

        # toggle fullscreen mode
        elif key == QtCore.Qt.Key_QuoteLeft:
            self.toggleFS()

        elif key == QtCore.Qt.Key_Right:
            self.toggleNext()

        elif key == QtCore.Qt.Key_Left:
            self.togglePrev()

        elif key == QtCore.Qt.Key_Up:
            self.toggleUp()

        elif key == QtCore.Qt.Key_Down:
            self.toggleDown()

        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    def closeEvent(self, evt):
        self.settings.setValue("geometry", self.saveGeometry());
        self.settings.setValue("windowState", self.saveState());

        for wid in self.WIDGETS:
            canClose = getattr(self.WIDGETS[wid], "canClose", lambda: True)
            if canClose() == False:
                evt.ignore()
                return

        evt.accept()
        for wid in self.WIDGETS:
            self.WIDGETS[wid].closeEvent(evt)
            if evt.isAccepted() == False:
                return

        for tbar in self.TOOLBARS:
            self.TOOLBARS[tbar].closeEvent(evt)
            if evt.isAccepted() == False:
                return

        QtGui.QMainWindow.closeEvent(self, evt)

    def quit(self):
        self.close()

def process_args():
    """
    Builds options dict.

    :return: ArgParse args object.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="dailies",
        description="""Q Dailies""",
        epilog="""
        """,
    )

    # input options
    input_group = parser.add_argument_group('Input')
    input_group.add_argument('-p', '--project',
                dest='project', action='store', required=False, type=str, default=os.environ.get('SHOW', ''),
                help='project name')
    input_group.add_argument('-s', '--shot',
                dest='shot', action='store', required=False, type=str, default=os.environ.get('SHOT', ''),
                help='shot name')

    args = parser.parse_args()
    return args

def main(args):
    app = QtGui.QApplication(sys.argv)
    win = QDailies(project=args.project, shot=args.shot)
    win.show()
    win.raise_()
    return app.exec_()

if __name__ == '__main__':
    try:
        args = process_args()
        sys.exit(main(args))
    except Exception, e:
        print e
    except KeyboardInterrupt:
        print 'Stopping...'
        sys.exit(1)

