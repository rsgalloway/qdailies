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
import copy
import time
import subprocess

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from qdailies.lib import config
from qdailies.lib import style
from qdailies.lib.fetch_image import URLImage
from qdailies.lib.qtree import QTreeWidget, QTreeWidgetItem
from qdailies.lib.threads import ShotgunVersionsThread, ShotgunThumbThread
from qdailies.lib.logger import log

class VersionTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, version, parent=None):
        super(VersionTreeWidgetItem, self).__init__(parent)
        self.version = version

        # column values
        self.handleThumb(config.DEFAULT_THUMB)
        self.setCheckState(self.treeWidget().colnum('load'), QtCore.Qt.Unchecked)
        self.setText(self.treeWidget().colnum('name'), (version.get('code') or ''))
        self.setText(self.treeWidget().colnum('status'), version.get(config.SG_FIELD_MAP.get('STATUS'), '-'))
        self.setText(self.treeWidget().colnum('date'), str(version.get('created_at').strftime("%m-%d-%Y %H:%M")))
        self.setText(self.treeWidget().colnum('description'), (version.get('description', '') or ''))
        self.setTextAlignment(self.treeWidget().colnum('status'), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.setTextColor(self.treeWidget().colnum('status'), QtGui.QColor(*config.STATUS_COLOR_MAP.get(version.get(config.SG_FIELD_MAP.get('STATUS')), 'default')))

        # movie paths
        self.left = version.get(config.SG_FIELD_MAP.get('MOVIE_LEFT'))
        self.right = version.get(config.SG_FIELD_MAP.get('MOVIE_RIGHT'))

    def __str__(self):
        return self.version.get('code', '')

    def __repr__(self):
        return "<Version '%s'>" % self.version.get('code', '')

    def __getattr__(self, attr):
        return getattr(self.version, attr, None)

    def get(self, attr):
        return self.version.get(attr, None)

    def handleThumb(self, thumb):
        if type(thumb) == URLImage:
            pixmap = QtGui.QPixmap.fromImage(thumb)
        elif os.path.isfile(thumb):
            pixmap = QtGui.QPixmap(thumb)
        else:
            return
        pixmap = pixmap.scaledToWidth(self.treeWidget().header().sectionSize(self.treeWidget().colnum('thumb')))
        if pixmap and not pixmap.isNull():
            self.setIcon(self.treeWidget().colnum('thumb'), QtGui.QIcon(pixmap))

    def handleThumbError(self, error):
        log.error('Error processing thumb: %s' % error)

class VersionTreeWidget(QTreeWidget):

    DEFAULT_COLUMN_NAMES  = ['load', 'thumb', 'name', 'status', 'date', 'description', ]

    DEFAULT_COLUMNS = dict(enumerate(DEFAULT_COLUMN_NAMES))
    DEFAULT_COLUMNS.update(dict(zip(DEFAULT_COLUMN_NAMES, range(len(DEFAULT_COLUMN_NAMES)))))
    COLUMNS = copy.copy(DEFAULT_COLUMNS)

    def __init__(self, parent, main):
        super(VersionTreeWidget, self).__init__(parent)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.main = main

    def setupHeader(self):
        self.setColumnCount(len(self.COLUMNS)/2)
        self.setHeaderLabels(self.columnNames)
        self.header().resizeSection(self.colnum('load'), 20)
        self.header().resizeSection(self.colnum('thumb'), 30)
        self.header().resizeSection(self.colnum('name'), 140)
        self.header().resizeSection(self.colnum('status') ,55)
        self.header().resizeSection(self.colnum('date'), 145)
        self.header().resizeSection(self.colnum('description'), 110)
        self.header().setResizeMode(self.colnum('load'), QtGui.QHeaderView.Fixed)
        self.header().setResizeMode(self.colnum('thumb'), QtGui.QHeaderView.Fixed)
        #QTreeWidget.setupHeader(self)

    def keyPressEvent(self, event):
        return self.main.keyPressEvent(event)

    def handleLoad(self, item):
        if item.checkState(self.colnum('load')):
            self.parent().parent().addToQueue(item)
        else:
            self.parent().parent().removeFromQueue(item)

class Tree(QtGui.QWidget):

    VERSION_QUEUE = []

    def __init__(self, parent=None, main=None):
        super(Tree, self).__init__(parent)
        uic.loadUi(os.path.join(config.UI_ROOT, 'tree.ui'), self)
        self.setStyleSheet(style.tree + style.scrollbar)
        self.setObjectName('tree')
        self.main = main

        self.vlayout = QtGui.QHBoxLayout()
        self.vlayout.setSpacing(0)
        self.vlayout.setMargin(0)
        self.versionBox.setLayout(self.vlayout)
        self.versionsTree = VersionTreeWidget(self, main=self.main)
        self.vlayout.addWidget(self.versionsTree)

        self.connect(self.versionsTree, QtCore.SIGNAL('itemSelectionChanged ()'), self.handleItemSelected)
        self.connect(self.versionsTree, QtCore.SIGNAL('itemDoubleClicked (QTreeWidgetItem *,int)'), self.handleItemDblClicked)
        self.connect(self.main, QtCore.SIGNAL('findVersions (PyQt_PyObject)'), self.handleGetVersions)
        self.connect(self.main, QtCore.SIGNAL('showQueue ()'), self.showQueue)
        self.connect(self.main, QtCore.SIGNAL('finished (PyQt_PyObject)'), self.handleNext)

        self.threads = []

    def queue(self):
        return self.VERSION_QUEUE

    def inQueue(self, version):
        return self.getQueueItem(version) is not None

    def getQueueItem(self, version):
        for item in self.queue():
            if item.get('id') == version.get('id'):
                return item

    def addToQueue(self, version):
        if not self.inQueue(version):
            log.debug('adding to queue: %s' % version)
            self.queue().append(version)
            self.emit(QtCore.SIGNAL('versionAddedtoQueue (PyQt_PyObject)'), version)

    def removeFromQueue(self, version):
        if self.inQueue(version):
            log.debug('removing from queue: %s' % version)
            del self.queue()[self.queue().index(version)]
            self.emit(QtCore.SIGNAL('versionRemovedFromQueue (PyQt_PyObject)'), version)

    def clear(self):
        _remove = []
        for item in self.versionsTree:
            if not self.inQueue(item):
                log.debug('removing %s' % item)
                _remove.append(item)
            else:
                log.debug('hiding %s' % item)
                item.setHidden(True)
        for item in _remove:
            self.versionsTree.removeItem(item)

    def showQueue(self):
        log.debug('showQueue')
        self.clear()
        for version in self.queue():
            version.setHidden(False)

    def getVersions(self, entity, task=None):
        """
        Gets a list of versions from shotgun using a thread.

        :param entity: shotgun entity dict
        :param task: shotgun task dict
        """
        if type(entity) is not dict:
            self.main.info('Invalid shot')
            return

        self.clear()
        self.versionsTree.setDisabled(True)
        self.versionsTree.setAlternatingRowColors(False)

        self._versionsThread = ShotgunVersionsThread(self, entity, task)
        self.connect(self._versionsThread, QtCore.SIGNAL("versions (PyQt_PyObject)"), self.handleVersions)
        self.connect(self._versionsThread, QtCore.SIGNAL("error (PyQt_PyObject)"), self.handleError)
        self._versionsThread.start()
        self.threads.append(self._versionsThread)

    def getThumb(self, item):
        """
        Gets a list of tasks from shotgun.

        :param shot: shot name (string)
        """
        self._thumbThread = ShotgunThumbThread(self, item.version)
        self.connect(self._thumbThread, QtCore.SIGNAL("thumb (PyQt_PyObject)"), item.handleThumb)
        self.connect(self._thumbThread, QtCore.SIGNAL("error (PyQt_PyObject)"), item.handleThumbError)
        self._thumbThread.start()
        self.threads.append(self._thumbThread)

    def handleError(self, error):
        self.main.info(error)

    def handleGetVersions(self, entity, task=None):
        """
        Handler for findVersions signal.

        :param entity: shotgun entity dict
        :param task: shotgun task dict
        """
        self.getVersions(entity, task)

    def handleVersions(self, versions):
        """
        Versions thread completion handler.

        :param: list of shotgun version entity dicts.
        """
        self.clear()

        for version in versions:
            item = self.getQueueItem(version)
            if item:
                item.setHidden(False)
            else:
                item = VersionTreeWidgetItem(version=version, parent=self.versionsTree)
                self.getThumb(item)

        self.versionsTree.setEnabled(True)
        self.versionsTree.setAlternatingRowColors(True)

    def handleItemSelected(self):
        versions = self.versionsTree.selectedItems()
        for version in versions:
            self.main.emit(QtCore.SIGNAL('load (PyQt_PyObject)'), version)

    def handleItemDblClicked(self, item, index):
        self.playVersion(item)

    def handleNext(self, version=None):
        self.versionsTree.selectNext()
        self.main.emit(QtCore.SIGNAL('play ()'))

    def handlePrev(self, version=None):
        self.versionsTree.selectPrev()
        self.main.emit(QtCore.SIGNAL('play ()'))

    def playVersion(self, version):
        """
        RV movie player, checks for left and right eyes.
        """
        left = version.left
        right = version.right
        if not left:
            self.main.info('Movie path not found')
        elif not os.path.exists(left):
            self.main.info('File not found:\n%s' % left)
        else:
            if not right:
                log.warning('Right-eye movie path not found')
                cmd = '%s %s' %(config.RV_PATH, left)
            else:
                cmd = '%s [ %s %s ] -stereo %s' %(config.RV_PATH, left, right, config.RV_STEREO_MODE)
            subprocess.Popen(cmd, shell=True)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Tree()
    win.show()
    win.raise_()
    sys.exit(app.exec_())
