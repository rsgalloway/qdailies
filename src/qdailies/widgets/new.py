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
import re
import sys
import copy
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

def edit2str(edit):
    # returns QLineEdit value as str
    return str(edit.text().toAscii())

def edit2int(edit):
    # returns QLineEdit value as int
    return int(edit.text().toAscii())

def edit2float(edit):
    # returns QLineEdit value as float
    return float(edit.text().toAscii())

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
        self.connect(self.btnCancel, QtCore.SIGNAL('pressed ()'), self.handleCancel)
        self.connect(self.btnSubmit, QtCore.SIGNAL('pressed ()'), self.handleSubmit)
        self.connect(self.slate, QtCore.SIGNAL('stateChanged (int)'), self.handleSlate)
        self.connect(self.qualitySlider, QtCore.SIGNAL('valueChanged (int)'), self.handleQualitySlider)
        self.connect(self.quality, QtCore.SIGNAL('valueChanged (int)'), self.handleQualitySpin)
        self.connect(self.showCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeShow)
        self.connect(self.shotCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeShot)
        self.connect(self.taskCombo, QtCore.SIGNAL('activated (const QString&)'), self.handleChangeTask)
        self.connect(self.out1ResCombo, QtCore.SIGNAL('currentIndexChanged (const QString&)'), self.handleOut1Res)
        self.connect(self.out2ResCombo, QtCore.SIGNAL('currentIndexChanged (const QString&)'), self.handleOut2Res)

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
            self.out1ResCombo.addItem(name)
            self.out2ResCombo.addItem(name)

        # set the default crop
        self.xmin.setText(str(config.RV_CROP[0]))
        self.ymin.setText(str(config.RV_CROP[1]))
        self.xmax.setText(str(config.RV_CROP[2]))
        self.ymax.setText(str(config.RV_CROP[3]))

        # set the default stereo right-eye convergence
        self.editConvergence.setText(str(config.RV_STEREO_OFFSET))

        self.editOut1.setText(config.DAILIES_MOVIE_PATH)
        self.editOut2.setText(config.DAILIES_AVID_PATH)
        self._toggleEditOut1()
        self._toggleEditOut2()

        self.setFocus()
        self.btnSubmit.setEnabled(False)
        self.btnFindRight.setEnabled(False)

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
        self.out1ResCombo.setHidden(hide)
        self.out1Width.setHidden(hide)
        self.out1Height.setHidden(hide)

    def _toggleEditOut2(self):
        hide = self.editOut2.isHidden()
        self.editOut2.setHidden(not hide)
        self.out2ResCombo.setHidden(hide)
        self.out2Width.setHidden(hide)
        self.out2Height.setHidden(hide)

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

    def handleOut1Res(self, scale):
        """
        Out1 res combo onchange handler.
        """
        xres, yres = config.RV_SCALE_OPTIONS.get(str(scale), (720, 480))
        self.out1Width.setText(str(xres))
        self.out1Height.setText(str(yres))

    def handleOut2Res(self, scale):
        """
        Out2 res combo onchange handler.
        """
        xres, yres = config.RV_SCALE_OPTIONS.get(str(scale), (720, 480))
        self.out2Width.setText(str(xres))
        self.out2Height.setText(str(yres))

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

    def getConvergence(self):
        """
        Looks for dragon take.xml file, and returns stereoConvR value.
        Reimplement in client forks based on workflow.
        """
        default = config.RV_STEREO_OFFSET
        if not self.seq_right:
            return default

        top = os.path.dirname(self.seq_right.path())
        done = False
        count = 0

        def _getStereoConvR(path):
            f = open(os.path.realpath(path), 'r')
            m = re.search(r'stereoConvR="(\d+.\d+)"', f.read())
            if m:
                return m.groups()[0]
            f.close()

        while not done:
            path = os.path.join(top, 'take.xml')
            if os.path.isfile(path):
                try:
                    return _getStereoConvR(path)
                except Exception, e:
                    log.debug(str(e))
                    return default
                done = True
            elif top != os.path.dirname(top):
                top = os.path.dirname(top)
            else:
                done = True
            count += 1
            if count > 5:
                break

        return default

    def handleFindLeft(self):
        """
        Left button handler.
        """
        r = str(QtGui.QFileDialog.getOpenFileName(self, "Find Left-Eye Sequence"))
        if not r:
            return
        self.setFileSequence(r, 'left')
        self.btnSubmit.setEnabled(True)
        self.btnFindRight.setEnabled(True)

    def handleFindRight(self):
        """
        Right button handler.
        """
        r = str(QtGui.QFileDialog.getOpenFileName(self, "Find Right-Eye Sequence"))
        if not r:
            return
        self.setFileSequence(r, 'right')
        self.editConvergence.setText(str(self.getConvergence()))

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
        self.labelConvergence.setHidden(toggle)
        self.editConvergence.setHidden(toggle)
        self.rightBar.setVisible(toggle)
        self.rightBar.setMinimum(0)
        self.rightBar.setMaximum(0)

    def handleKillThreads(self):
        """
        Stops all threads.
        """
        for thread in self.threads:
            if thread.isRunning():
                thread.terminate()

    def handleThreadStart(self, data):
        """
        thread start handler
        """
        name, eye = data
        log.debug('handleThreadStart: %s %s' % (name, eye))
        self.btnSubmit.setEnabled(False)
        self.btnFindLeft.setEnabled(False)
        self.btnFindRight.setEnabled(False)
        if eye == 'left':
            self.toggleLeftProgress(True)
        elif eye == 'right':
            self.toggleRightProgress(True)

    def handleThreadComplete(self, path):
        """
        Thread completion handler.
        """
        log.debug('handleThreadComplete: %s' % path)
        all_done = True
        left_done = True
        right_done = True

        for thread in self.threads:

            # skip running threads
            if thread.isAlive():
                all_done = False
                if thread.eye == 'left':
                    left_done = False
                elif thread.eye == 'right':
                    right_done = False
                continue

            # update left eye movie path
            elif thread.eye == 'left' and thread.name == 'movie':
                params = {config.SG_FIELD_MAP.get('MOVIE_LEFT'): path}
                log.debug('update left: %s' % params)
                updateEntity(self.sg_version_dict, params)

            # update right eye movie path
            elif thread.eye == 'right' and thread.name == 'movie':
                params = {config.SG_FIELD_MAP.get('MOVIE_RIGHT'): path}
                log.debug('update right: %s' % params)
                updateEntity(self.sg_version_dict, params)

            # update left eye frames path
            elif thread.eye == 'left' and thread.name == 'frames':
                params = {config.SG_FIELD_MAP.get('FRAMES_LEFT'): path}
                log.debug('update left: %s' % params)
                updateEntity(self.sg_version_dict, params)

            # update right eye frames path
            elif thread.eye == 'right' and thread.name == 'frames':
                params = {config.SG_FIELD_MAP.get('FRAMES_RIGHT'): path}
                log.debug('update right: %s' % params)
                updateEntity(self.sg_version_dict, params)

            # remove completed threads from queue
            self.threads.remove(thread)

        if left_done:
            self.toggleLeftProgress(False)

        if right_done:
            self.toggleRightProgress(False)

        if all_done:
            self.btnSubmit.setEnabled(True)
            self.btnFindLeft.setEnabled(True)
            self.btnFindRight.setEnabled(True)

    def addThread(self, klass, seq, params):
        """
        create and start a new thread

        :param klass: threads.py thread classs
        :param seq: file sequence arg to pass to thread
        :param params: params dict to pass to thread
        """
        log.debug('addThread: %s %s %s' % (klass, seq, params))
        if not klass or not seq:
            return
        thread = klass(self, seq, params)
        self.connect(thread, QtCore.SIGNAL('start (PyQt_PyObject)'), self.handleThreadStart)
        self.connect(thread, QtCore.SIGNAL('complete (PyQt_PyObject)'), self.handleThreadComplete)
        self.connect(thread, QtCore.SIGNAL('error (PyQt_PyObject)'), self.handleError)
        self.threads.append(thread)
        thread.start()
        return thread

    def handleCancel(self):
        """
        Close button handler.
        """
        self.handleKillThreads()
        self.close()

    def handleSubmit(self):
        """
        Submit button handler.
        """
        if not self.seq_left:
            self.info('Click the Left button to choose a frame sequence')
            return

        # initialize some vars
        self.threads = []
        source_left = None
        source_right = None

        # the shotgun versions entity dict which we will update later
        # as the threads complete
        self.sg_version_dict = {}

        # default params
        out1_lt_params = {'eye': 'left'}
        out1_rt_params = {'eye': 'right'}
        out2_lt_params = {'eye': 'left'}
        out2_rt_params = {'eye': 'right'}

        # get the shotgun entities
        sg_show = self._shows.get(str(self.showCombo.currentText().toAscii()), None)
        sg_shot = self._shots.get(str(self.shotCombo.currentText().toAscii()), None)
        sg_task = self._tasks.get(str(self.taskCombo.currentText().toAscii()), None)

        if not sg_show or not sg_shot:
            self.info('Show and Shot are required arguments')
            return

        # disable submit button
        self.btnSubmit.setEnabled(False)

        # set some shotgun data
        show = sg_show.get(config.SG_FIELD_MAP.get('SHOW'))
        shot = sg_shot.get(config.SG_FIELD_MAP.get('NAME'))
        seq = shot.split('_')[0]
        task = sg_task.get(config.SG_FIELD_MAP.get('TASK'))
        out1_lt_params.update(show=show, shot=shot, sequence=seq, task=task)
        out1_rt_params.update(show=show, shot=shot, sequence=seq, task=task)
        out2_lt_params.update(show=show, shot=shot, sequence=seq, task=task)
        out2_rt_params.update(show=show, shot=shot, sequence=seq, task=task)

        # left-eye source
        source_left = os.path.join(os.path.dirname(self.seq_left.path()), edit2str(self.leftEdit))
        out1_lt_params.update(leftFramesPath=source_left)
        out2_lt_params.update(leftFramesPath=source_left)

        # right-eye source
        if self.seq_right:
            source_right = os.path.join(os.path.dirname(self.seq_right.path()), edit2str(self.rightEdit))
            out1_rt_params.update(rightFramesPath=source_right)
            out2_rt_params.update(rightFramesPath=source_right)

        # set dailies status on out1_lt
        if self.dailies.checkState():
            out1_lt_params.update(status='rev')
            out1_rt_params.update(status='rev')
            out2_lt_params.update(status='rev')
            out2_rt_params.update(status='rev')

        # slate options
        if self.slate.checkState():
            out1_lt_params.update(slate=True, comment=edit2str(self.comment))
            out1_rt_params.update(slate=True, comment=edit2str(self.comment))
            out2_lt_params.update(slate=True, comment=edit2str(self.comment))
            out2_rt_params.update(slate=True, comment=edit2str(self.comment))

        # output resolutions
        out1xres, out1yres = (edit2int(self.out1Width), edit2int(self.out1Height))
        out2xres, out2yres = (edit2int(self.out2Width), edit2int(self.out2Height))
        out1_lt_params.update(width=out1xres, height=out1yres)
        out1_rt_params.update(width=out1xres, height=out1yres)
        out2_lt_params.update(width=out2xres, height=out2yres)
        out2_rt_params.update(width=out2xres, height=out2yres)

        # crops
        if self.crop.checkState():
            lt_crop_xmin = edit2int(self.xmin)
            lt_crop_ymin = edit2int(self.ymin)
            lt_crop_xmax = edit2int(self.xmax)
            lt_crop_ymax = edit2int(self.ymax)
            out1_lt_params.update(crop=(lt_crop_xmin, lt_crop_ymin, lt_crop_xmax, lt_crop_ymax))
            out2_lt_params.update(crop=(lt_crop_xmin, lt_crop_ymin, lt_crop_xmax, lt_crop_ymax))

            # HACK: hardcoded input width, should come from source
            offset = int(config.RV_INPUT_WIDTH * edit2float(self.editConvergence))
            rt_crop_xmin = lt_crop_xmin + offset
            rt_crop_ymin = lt_crop_ymin
            rt_crop_xmax = lt_crop_xmax + offset
            rt_crop_ymax = lt_crop_ymax
            out1_rt_params.update(crop=(rt_crop_xmin, rt_crop_ymin, rt_crop_xmax, rt_crop_ymax))
            out2_rt_params.update(crop=(rt_crop_xmin, rt_crop_ymin, rt_crop_xmax, rt_crop_ymax))

        # quality
        quality = int(self.quality.value())
        out1_lt_params.update(quality=quality)
        out1_rt_params.update(quality=quality)
        out2_lt_params.update(quality=quality)
        out2_rt_params.update(quality=quality)

        # create take in shotgun, we need id and rev number for pathing
        sg_params = copy.copy(out1_lt_params)
        sg_params.update(rightFramesPath=source_right)
        self.sg_version_dict = makeTake(**sg_params)
        if not self.sg_version_dict:
            self.info('Error creating take in shotgun')
            return
        sg_id_no = self.sg_version_dict.get('id')
        sg_take_no = self.sg_version_dict.get(config.SG_FIELD_MAP.get('TAKE_NUMBER'))

        # create the thumbnail, ignoring errors
        thumbThread = ThumbThread(self, source_left, sg_id_no)
        thumbThread.start()

        # set version number
        out1_lt_params.update(version=sg_take_no)
        out1_rt_params.update(version=sg_take_no)
        out2_lt_params.update(version=sg_take_no)
        out2_rt_params.update(version=sg_take_no)

        # set the outfile param
        out1_lt_params.update(outfile=config.DAILIES_MOVIE_PATH % out1_lt_params)
        out1_rt_params.update(outfile=config.DAILIES_MOVIE_PATH % out1_rt_params)
        out2_lt_params.update(outfile=config.DAILIES_AVID_PATH % out2_lt_params)
        out2_rt_params.update(outfile=config.DAILIES_AVID_PATH % out2_rt_params)

        # create out1 threads
        out1_lt_thread = self.addThread(DailyThread, source_left, out1_lt_params)
        out1_rt_thread = self.addThread(DailyThread, source_right, out1_rt_params)

        # create out2 threads
        if self.out2.checkState():
            out2_lt_thread = self.addThread(AvidThread, source_left, out2_lt_params)
            out2_rt_thread = self.addThread(AvidThread, source_right, out2_rt_params)

def main():
    app = QtGui.QApplication(sys.argv)
    win = NewVersionWidget()
    win.show()
    win.raise_()
    win.getShows()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
