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
from qdailies.lib.threads import ShotgunVersionsThread
from qdailies.lib.logger import log

class QAction(QtGui.QAction):

    def __init__(self, parent, name, **kwargs):
        super(QAction, self).__init__(parent)
        self.setText(name)
        self.name = name
        self.icon = kwargs.get('icon', None)
        self.obj = kwargs.get('object', None)
        self.func = kwargs.get('func', None)
        self.col = kwargs.get('col', None)
        self.attrs = kwargs.get('attrs',None)
        self.highlight = kwargs.get('highlight', False)
        self.selected = kwargs.get('selected', None)
        self.setCheckable(False)
        self.allowedTypes = kwargs.get('allowedTypes', None)
        self.yesToAll = False

        if self.highlight:
            self.setCheckable(True)
            self.setChecked(True)

        if self.icon:
            self.setIcon(self.icon)

        if self.selected:
            itemTypeList = [item.apiObj.imd_type for item in self.selected]
            self.setEnabled(self.allowedTypes in itemTypeList)

        if parent:
            self.parent().addAction(self)

    def setIcon(self, iconPath=None):
        if not iconPath:
            iconPath = os.path.join(config.GFX_ROOT, 'movie_clip.png')
        self.icon = iconPath
        QtGui.QAction.setIcon(self, QtGui.QIcon(self.icon))

class QTreeWidgetItem(QtGui.QTreeWidgetItem):

    def __init__(self, parent=None):
        super(QTreeWidgetItem, self).__init__(parent)
        self.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.DontShowIndicator)
        self.setExpanded(False)

class QHeader(QtGui.QHeaderView):

    def __init__(self, parent, **kwargs):
        super(QHeader, self).__init__(QtCore.Qt.Horizontal, parent)
        self.setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.setStretchLastSection(True)

    def mouseReleaseEvent(self, event):
        QtGui.QHeaderView.mouseReleaseEvent(self, event)

        menu = QtGui.QMenu(self)
        menu_action = None

        if event.button() == QtCore.Qt.RightButton:
            self.connect(menu, QtCore.SIGNAL("triggered(QAction *)"), self.doMenuAction)
            menu_action = True

            for col in self.parent().columnNames:
                if col in ['load', 'state']:
                    continue
                act = QAction(menu, name=str(col), func=self.toggleColumn, col=str(col))
                if self.parent().isColumnHidden(self.parent().colnum(col)):
                    act.setIcon(os.path.join(config.GFX_ROOT, 'icon.unchecked.png'))
                else:
                    act.setIcon(os.path.join(config.GFX_ROOT, 'icon.checked.png'))
                menu.addAction(act)

        if menu_action:
            position = self.mapToGlobal(QtCore.QPoint(0,0))
            position.setX(position.x() + event.pos().x())
            position.setY(position.y() + event.pos().y()+10)
            menu.popup(position)

    def toggleColumn(self, action):
        self.parent().toggleColumn(action.col)

    def doMenuAction(self, action):
        """handle context menu actions by calling their function"""
        if hasattr(action, 'func'):
            action.func(action)

    def restoreState(self):
        return
        state = self.parent().main.prefs.get('UI', str(self.parent().objectName()))
        if state != '':
            data = QtCore.QByteArray()
            data = data.fromBase64(state)
            QtGui.QHeaderView.restoreState(self, data)

class QTreeWidget(QtGui.QTreeWidget):

    DEFAULT_COLUMN_NAMES  = ['load', 'thumb', 'name', 'status', 'date', 'description', ]

    DEFAULT_COLUMNS = dict(enumerate(DEFAULT_COLUMN_NAMES))
    DEFAULT_COLUMNS.update(dict(zip(DEFAULT_COLUMN_NAMES, range(len(DEFAULT_COLUMN_NAMES)))))
    COLUMNS = copy.copy(DEFAULT_COLUMNS)

    def colnum(self, name):
        return self.COLUMNS.get(name, -1)

    @property
    def columnNames(self):
        return [self.COLUMNS[elm] for elm in sorted(elm for elm in self.COLUMNS if type(elm) == int)]

    def __init__(self, parent=None):
        super(QTreeWidget, self).__init__(parent)
        self.setIconSize(QtCore.QSize(20, 20))
        self.setAllColumnsShowFocus(True)
        self.setAnimated(True)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)

        self.setHeader(QHeader(self))
        self.initHeader()

        self.connect(self, QtCore.SIGNAL("itemClicked (QTreeWidgetItem *, int)"), self.handleClick)

    def __iter__(self):
        for i in xrange(self.topLevelItemCount()):
            yield self.topLevelItem(i)

    def setColumnNames(self, nameList):
        self.DEFAULT_COLUMN_NAMES = nameList
        self.DEFAULT_COLUMNS = dict(enumerate(self.DEFAULT_COLUMN_NAMES))
        self.DEFAULT_COLUMNS.update(dict(zip(self.DEFAULT_COLUMN_NAMES, range(len(self.DEFAULT_COLUMN_NAMES)))))
        self.COLUMNS = copy.copy(self.DEFAULT_COLUMNS)

    def setHeaderLabels(self, labels):
        #TODO: look for icon
        _labs = []
        for lab in labels:
            if lab in ['load', 'state', 'thumb']:
                lab = ''
            _labs.append(lab)
        QtGui.QTreeWidget.setHeaderLabels(self, _labs)

    def clearTree(self, tree):
        for ch in tree.takeChildren():
            tree.removeChild(ch)

    def clear(self):
        QtGui.QTreeWidget.clear(self)

    def selectNext(self):
        items = self.selectedItems()
        if len(items) > 0:
            idx = self.indexOfTopLevelItem(items[-1])
        else:
            idx = -1
        if 0 <= (idx+1) <= self.topLevelItemCount():
            self.setItemSelected(self.topLevelItem(idx), False)
            self.setItemSelected(self.topLevelItem(idx+1), True)

    def selectPrev(self):
        items = self.selectedItems()
        if len(items) > 0:
            idx = self.indexOfTopLevelItem(items[-1])
        else:
            idx = 1
        if self.topLevelItemCount() >= (idx-1) >= 0:
            self.setItemSelected(self.topLevelItem(idx), False)
            self.setItemSelected(self.topLevelItem(idx-1), True)

    def removeItem(self, item):
        idx = self.indexOfTopLevelItem(item)
        self.takeTopLevelItem(idx)

    def initHeader(self):
        self.COLUMNS = copy.copy(self.DEFAULT_COLUMNS)
        self.setupHeader()
        self.setSortingEnabled(True)
        self.sortByColumn(self.colnum('date'), QtCore.Qt.DescendingOrder)

    def setupHeader(self):
        self.header().restoreState()
        self.connect(self.header(), QtCore.SIGNAL("sectionResized (int,int,int)"), self.header().saveHeaderState)

    def handleClick(self, item, col):
        """determine what method to call based on the col that was clicked"""
        if item.isDisabled():
            return
        if col == self.colnum('load'):
            self.handleLoad(item)
        elif col == self.colnum('state'):
            self.handleState(item)
        else:
            return
