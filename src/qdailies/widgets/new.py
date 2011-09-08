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
import time
import subprocess

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from qdailies.lib.threads import *
from qdailies.lib.sglib import getSequence
from qdailies.lib.logger import log
from qdailies.lib import config
from qdailies.lib import style

class NewVersionWidget(QtGui.QDialog):

    def __init__(self):
        super(NewVersionWidget, self).__init__()
        uic.loadUi(os.path.join(config.UI_ROOT, 'new.ui'), self)
        self.setWindowTitle('NewQ')
        self.setStyle(QtGui.QStyleFactory.create('cleanlooks'))
        self.setStyleSheet(style.new + style.scrollbar)

        self.toggleLeftProgress(False)
        self.toggleRightProgress(False)

        self.connect(self.btnFindLeft, QtCore.SIGNAL('pressed ()'), self.handleFindLeft)
        self.connect(self.btnFindRight, QtCore.SIGNAL('pressed ()'), self.handleFindRight)
        self.connect(self.btnCancel, QtCore.SIGNAL('pressed ()'), self.close)
        self.connect(self.btnSubmit, QtCore.SIGNAL('pressed ()'), self.handleSubmit)
        self.connect(self.slate, QtCore.SIGNAL('stateChanged (int)'), self.handleSlate)
        self.connect(self.qualitySlider, QtCore.SIGNAL('valueChanged (int)'), self.handleQualitySlider)
        self.connect(self.quality, QtCore.SIGNAL('valueChanged (int)'), self.handleQualitySpin)
        self.connect(self.showCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeShow)
        self.connect(self.shotCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeShot)
        self.connect(self.taskCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeTask)
        self.connect(self.scaleCombo, QtCore.SIGNAL('currentIndexChanged (const QString&)'), self.handleChangeScale)
        self.connect(self.avidCombo, QtCore.SIGNAL('currentIndexChanged (const QString&)'), self.handleChangeAvid)

        self.connect(self.btnToggleOut1, QtCore.SIGNAL('pressed ()'), self._toggleEditOut1)
        self.connect(self.btnToggleOut2, QtCore.SIGNAL('pressed ()'), self._toggleEditOut2)

        # defaults
        self._shows = {}
        self._shots = {}
        self._tasks = {}
        self.threads = []
        self.seq_left = None
        self.seq_right = None
        self.showCombo.setEnabled(False)
        self.shotCombo.setEnabled(False)
        self.quality.setValue(config.RV_QUALITY * 100)

        for name, res in sorted((k, (v[0], v[1])) for k, v in config.RV_SCALE_OPTIONS.items()):
            self.scaleCombo.addItem(name)
            self.avidCombo.addItem(name)

        # set the default crop
        self.xmin.setText(str(config.RV_CROP[0]))
        self.ymin.setText(str(config.RV_CROP[1]))
        self.xmax.setText(str(config.RV_CROP[2]))
        self.ymax.setText(str(config.RV_CROP[3]))

        self.editOut1.setText(config.DAILIES_MOVIE_PATH)
        self.editOut2.setText(config.DAILIES_AVID_PATH)
        self._toggleEditOut1()
        self._toggleEditOut2()

        self.setFocus()

    def info(self, msg="Error", title="Error"):
        """
        Creates a Qt message box with msg and title.
        """
        dialog = QtGui.QMessageBox()
        dialog.information(self, title, msg)

    def prompt(self, msg, title="Warning", multi=False):    
        """
        Generic question dialog box.

        :return: QtGui.QMessageBox.Yes/No
        """
        dialog = QtGui.QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(msg)
        dialog.addButton(QtGui.QMessageBox.Yes)
        if multi:
            dialog.addButton(QtGui.QMessageBox.YesToAll)
        dialog.addButton(QtGui.QMessageBox.No)
        dialog.addButton(QtGui.QMessageBox.Cancel)
        return dialog.exec_()

    def _setComboError(self, combo, error):
        """
        Updates a combo box with error indicator.
        """
        combo.setStyleSheet('background-color: #990; color: #111;')
        combo.setEnabled(False)
        combo.clear()
        combo.addItem('There was an error')
        self.info(error, title='Error')

    def handleError(self, error):
        self.toggleLeftProgress(False)
        self.toggleRightProgress(False)
        self.info(msg=error, title='Error')
        self.handleKillThreads()

    def handleShowsError(self, error):
        """
        Handles errors when getting shows from shotgun.
        """
        self._setComboError(self.showCombo, error)

    def handleShotsError(self, error):
        """
        Handles errors when getting shots from shotgun.
        """
        self._setComboError(self.shotCombo, error)

    def handleTasksError(self, error):
        """
        Handles errors when getting tasks from shotgun.
        """
        self._setComboError(self.taskCombo, error)

    def handleShows(self, shows):
        """
        Shows thread completion handler.
        """
        self._shows = {}
        self.showCombo.clear()
        self.showCombo.setStyleSheet('background-color: #333437')
        self.showCombo.setEnabled(False)
        for show in shows:
            self._shows[str(show.get('name'))] = show
            self.showCombo.addItem(show.get('name'))
        self.showCombo.setEnabled(True)
        self.handleChangeShow()

    def handleShots(self, shots):
        """
        Shots thread completion handler.
        """
        self._shots = {}
        self.shotCombo.clear()
        self.shotCombo.setStyleSheet('background-color: #333437')
        self.shotCombo.setEnabled(False)
        for shot in shots:
            self._shots[str(shot.get('code'))] = shot
            self.shotCombo.addItem(shot.get('code'))
        self.shotCombo.setEnabled(True)
        self.handleChangeShot()

    def handleTasks(self, tasks):
        """
        Tasks thread completion handler.
        """
        self._tasks = {}
        self.taskCombo.clear()
        self.taskCombo.setStyleSheet('background-color: #333437')
        self.taskCombo.setEnabled(False)
        for task in tasks:
            self._tasks[str(task.get('content'))] = task
            self.taskCombo.addItem(task.get('content'))
        self.taskCombo.setEnabled(True)

    def _toggleComboLoadState(self, combo, loading=True):
        combo.clear()
        if loading:
            combo.addItem('Loading..')
            combo.setStyleSheet('background-color: #2a2; color: #141;')
            combo.setEnabled(False)
        else:
            combo.setStyleSheet('background-color: #333437; color: 999;')
            combo.setEnabled(True)

    def _toggleEditOut1(self):
        hide = self.editOut1.isHidden()
        self.editOut1.setHidden(not hide)
        self.scaleCombo.setHidden(hide)
        self.outresX.setHidden(hide)
        self.outresY.setHidden(hide)

    def _toggleEditOut2(self):
        hide = self.editOut2.isHidden()
        self.editOut2.setHidden(not hide)
        self.avidCombo.setHidden(hide)
        self.avidOutresX.setHidden(hide)
        self.avidOutresY.setHidden(hide)

    def getShows(self):
        """
        Gets a list of shows from shotgun.
        """
        self._toggleComboLoadState(self.showCombo, loading=True)
        self._toggleComboLoadState(self.shotCombo, loading=False)
        self._toggleComboLoadState(self.taskCombo, loading=False)

        self._showsThread = ShotgunShowsThread(self)
        self.connect(self._showsThread, QtCore.SIGNAL("shows (PyQt_PyObject)"), self.handleShows)
        self.connect(self._showsThread, QtCore.SIGNAL("error (PyQt_PyObject)"), self.handleShowsError)
        self._showsThread.start()
        self.threads.append(self._showsThread)

    def getShots(self, show):
        """
        Gets a list of shots from shotgun.

        :param show: show name (string)
        """
        self._toggleComboLoadState(self.shotCombo, loading=True)
        self._toggleComboLoadState(self.taskCombo, loading=False)

        self._shotsThread = ShotgunShotsThread(self, self._shows.get(show))
        self.connect(self._shotsThread, QtCore.SIGNAL("shots (PyQt_PyObject)"), self.handleShots)
        self.connect(self._shotsThread, QtCore.SIGNAL("error (PyQt_PyObject)"), self.handleShotsError)
        self._shotsThread.start()
        self.threads.append(self._shotsThread)

    def getTasks(self, shot):
        """
        Gets a list of tasks from shotgun.

        :param shot: shot name (string)
        """
        self._toggleComboLoadState(self.taskCombo, loading=True)

        self._tasksThread = ShotgunTasksThread(self, self._shots.get(shot))
        self.connect(self._tasksThread, QtCore.SIGNAL("tasks (PyQt_PyObject)"), self.handleTasks)
        self.connect(self._tasksThread, QtCore.SIGNAL("error (PyQt_PyObject)"), self.handleTasksError)
        self._tasksThread.start()
        self.threads.append(self._tasksThread)

    def handleChangeShow(self, show=None):
        """
        Show combo onchange handler.
        """
        if show is None:
            show = str(self.showCombo.currentText().toAscii())
        if not show:
            return
        self.getShots(str(show))

    def handleChangeShot(self, shot=None):
        """
        Shot combo onchange handler.
        """
        if shot is None:
            shot = str(self.shotCombo.currentText().toAscii())
        if not shot:
            return
        self.getTasks(str(shot))

    def handleChangeTask(self, task=None):
        """
        Task combo onchange handler.
        """
        pass

    def handleChangeScale(self, scale):
        """
        Scale combo onchange handler.
        """
        xres, yres = config.RV_SCALE_OPTIONS.get(str(scale), (720, 480))
        self.outresX.setText(str(xres))
        self.outresY.setText(str(yres))

    def handleChangeAvid(self, scale):
        """
        Scale combo onchange handler.
        """
        xres, yres = config.RV_SCALE_OPTIONS.get(str(scale), (720, 480))
        self.avidOutresX.setText(str(xres))
        self.avidOutresY.setText(str(yres))

    def handleSlate(self, state):
        """
        Slate checkbox click handler.
        """
        self.comment.setEnabled(state == QtCore.Qt.Checked)

    def handleQualitySlider(self, value):
        """
        Update the quality spin box according to the quality slider.
        """
        self.quality.setValue(value)

    def handleWidthSlider(self, value):
        """
        Update the width spin box according to the width slider.
        """
        self.width.setValue(value)

    def handleQualitySpin(self, value):
        """
        Update the quality slider according to the quality spin box.
        """
        self.qualitySlider.setValue(value)

    def handleFindLeft(self):
        """
        Left button handler.
        """
        r = str(QtGui.QFileDialog.getOpenFileName(self, "Find Left-Eye Sequence"))
        if not r:
            return
        self.setFileSequence(r, 'left')

    def handleFindRight(self):
        """
        Right button handler.
        """
        r = str(QtGui.QFileDialog.getOpenFileName(self, "Find Right-Eye Sequence"))
        if not r:
            return
        self.setFileSequence(r, 'right')

    def handleKillThreads(self):
        """
        Stops all threads.
        """
        for thread in self.threads:
            if thread.isRunning():
                thread.terminate()

    def setFileSequence(self, filepath, eye='left'):
        """
        Process the user input file sequence. 
        """
        _seq = getSequence(filepath)

        if not _seq:
            r = self.prompt('File is not part of a sequence. Proceed?')
            if r != QtGui.QMessageBox.Yes:
                return
            else:
                _seq = filepath
                _seqf = os.path.basename(filepath)
        else:
            _seqf = _seq.format(config.RV_SEQ_FORMAT)

        if eye == 'left':
            self.seq_left = _seq
            self.leftEdit.setText(_seqf)
        elif eye == 'right':
            self.seq_right = _seq
            self.rightEdit.setText(_seqf)

        self.slate.setEnabled(True)
        self.dailies.setEnabled(True)

    def toggleLeftProgress(self, toggle):
        """
        Toggles the visibilty of the progress bar for the left-eye.
        """
        self.leftEdit.setHidden(toggle)
        self.leftBar.setVisible(toggle)
        self.leftBar.setMinimum(0)
        self.leftBar.setMaximum(0)

    def toggleRightProgress(self, toggle):
        """
        Toggles the visibilty of the progress bar for the right-eye.
        """
        self.rightEdit.setHidden(toggle)
        self.rightBar.setVisible(toggle)
        self.rightBar.setMinimum(0)
        self.rightBar.setMaximum(0)

    def handleLeftComplete(self, leftMoviePath):
        """
        Movie thread completion handler, for left-eye movie.
        """
        # update shotgun with file paths
        params = {
            config.SG_FIELD_MAP.get('MOVIE_LEFT'): leftMoviePath,
        }
        updateEntity(self.sg_version_dict, params)
        self.btnSubmit.setEnabled(True)

        if not self.avid.checkState():
            self.toggleLeftProgress(False)
            self.btnFindLeft.setEnabled(True)

    def handleRightComplete(self, rightMoviePath):
        """
        movie thread completion handler, for right-eye movie.
        """
        # update shotgun with file paths
        params = {
            config.SG_FIELD_MAP.get('MOVIE_RIGHT'): rightMoviePath,
        }
        updateEntity(self.sg_version_dict, params)
        if not self.avid.checkState():
            self.toggleRightProgress(False)
            self.btnFindRight.setEnabled(True)

    def handleLeftAvidComplete(self, avidPath):
        self.toggleLeftProgress(False)
        self.btnFindLeft.setEnabled(True)

    def handleRightAvidComplete(self, avidPath):
        self.toggleRightProgress(False)
        self.btnFindRight.setEnabled(True)

    def handleSubmit(self):
        """
        Submit button handler. Launches threaded makeMov processes.
        """
        options = {}

        if not self.seq_left:
            self.info('Click the Left button to choose a frame sequence')
            return

        # get the shotgun entities
        _show = self._shows.get(str(self.showCombo.currentText().toAscii()), None)
        _shot = self._shots.get(str(self.shotCombo.currentText().toAscii()), None)
        _task = self._tasks.get(str(self.taskCombo.currentText().toAscii()), None)

        if not _show or not _shot or not _task:
            self.info('Be sure to select a show, shot and task')
            return

        options.update(show=_show.get(config.SG_FIELD_MAP.get('SHOW')))
        options.update(shot=_shot.get(config.SG_FIELD_MAP.get('NAME')))
        options.update(task=_task.get(config.SG_FIELD_MAP.get('TASK')))

        # left-eye
        _name_left = str(self.leftEdit.text().toAscii())
        _base_left = os.path.dirname(self.seq_left.path())
        _left = os.path.join(_base_left, _name_left)
        options.update(leftFramesPath=_left)
        log.debug('left: %s' % _left)

        # right-eye
        if self.seq_right:
            _name_right = str(self.rightEdit.text().toAscii())
            _base_right = os.path.dirname(self.seq_right.path())
            _right = os.path.join(_base_right, _name_right)
            options.update(rightFramesPath=_right)
            log.debug('right: %s' % _right)

        # dailies options
        if self.dailies.checkState():
            options.update(status='rev')

        # slate options
        if self.slate.checkState():
            options.update(slate=True, comment=str(self.comment.text().toAscii()))

        # crop
        if self.crop.checkState():
            xmin = int(self.xmin.text().toAscii())
            ymin = int(self.ymin.text().toAscii())
            xmax = int(self.xmax.text().toAscii())
            ymax = int(self.ymax.text().toAscii())
            options.update(resize=(xmax, ymax))
            options.update(crop=(xmin, ymin, xmax, ymax))

        # scale
        if self.scale.checkState():
            options.update(width=int(self.outresX.text()))
            options.update(height=int(self.outresY.text()))

        # quality
        options.update(quality=int(self.quality.value()))

        options.update(runRv=False)

        try:
            options.update(sequence=_shot.get(config.SG_FIELD_MAP.get('NAME')).split('_')[0])
        except IndexError, e:
            log.warning('sequence not found: %s' % str(e))

        # toggle progress bar
        self.btnFindLeft.setEnabled(False)
        self.btnSubmit.setEnabled(False)
        self.toggleLeftProgress(True)

        # create take in shotgun
        self.sg_version_dict = makeTake(**options)

        # thumb thread
        self._thumbThread = ThumbThread(self, _left, self.sg_version_dict.get('id'))
        self.connect(self._thumbThread, QtCore.SIGNAL('error (PyQt_PyObject)'), self.handleError)
        self._thumbThread.start()

        # update options with version number
        options.update(version=self.sg_version_dict.get(config.SG_FIELD_MAP.get('TAKE_NUMBER')))

        # left-eye thread
        _left_params = dict(options, **{'eye': 'left'})
        _left_params.update(outfile=str(self.editOut1.text().toAscii()) % _left_params)
        self._leftMovieThread = DailyThread(self, _left, _left_params)
        self.connect(self._leftMovieThread, QtCore.SIGNAL('complete (PyQt_PyObject)'), self.handleLeftComplete)
        self.connect(self._leftMovieThread, QtCore.SIGNAL('error (PyQt_PyObject)'), self.handleError)
        self._leftMovieThread.start()

        # generate avid left-eye frames
        if self.avid.checkState():
            _left_avid_params = dict(options, **{'eye': 'left'})
            _left_avid_params.update(outfile=str(self.editOut2.text().toAscii()) % _left_avid_params)
            self._leftAvidThread = AvidThread(self, _left, _left_avid_params)
            self.connect(self._leftAvidThread, QtCore.SIGNAL('complete (PyQt_PyObject)'), self.handleLeftAvidComplete)
            self.connect(self._leftAvidThread, QtCore.SIGNAL('error (PyQt_PyObject)'), self.handleError)
            self._leftAvidThread.start()

        # right eye
        if self.seq_right:
            self.btnFindRight.setEnabled(False)
            self.toggleRightProgress(True)
            _right_params = dict(options, **{'eye': 'right'})
            _right_params.update(outfile=str(self.editOut1.text().toAscii()) % _right_params)
            self._rightMovieThread = DailyThread(self, _right, _right_params)
            self.connect(self._rightMovieThread, QtCore.SIGNAL('complete (PyQt_PyObject)'), self.handleRightComplete)
            self.connect(self._rightMovieThread, QtCore.SIGNAL('error (PyQt_PyObject)'), self.handleError)
            self._rightMovieThread.start()

            # generate avid right-eye frames
            if self.avid.checkState():
                _right_avid_params = dict(options, **{'eye': 'right'})
                _right_avid_params.update(outfile=str(self.editOut2.text().toAscii()) % _right_avid_params)
                self._rightAvidThread = AvidThread(self, _right, _right_avid_params)
                self.connect(self._rightAvidThread, QtCore.SIGNAL('complete (PyQt_PyObject)'), self.handleRightAvidComplete)
                self.connect(self._rightAvidThread, QtCore.SIGNAL('error (PyQt_PyObject)'), self.handleError)
                self._rightAvidThread.start()

def main():
    app = QtGui.QApplication(sys.argv)
    win = NewVersionWidget()
    win.show()
    win.raise_()
    win.getShows()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
