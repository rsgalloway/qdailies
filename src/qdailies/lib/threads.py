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
import urllib
import subprocess
from socket import gaierror, getaddrinfo, getdefaulttimeout

from PyQt4 import QtCore
from PyQt4 import QtGui

from qdailies.lib.dailies import makeTake, makeMov, makeDaily, makeAvid, makeThumb
from qdailies.lib.fetch_image import URLImage
from qdailies.lib.sglib import *
from qdailies.lib.logger import log
from qdailies.lib import config

class ShotgunThreadMixin(object):
    """
    Timer mixin class for timing out connection issues with shotgun.
    """
    def timerEvent(self, event):
        print "Can't reach shotgun, stopping..."
        self.quit()

class ShotgunShowsThread(QtCore.QThread, ShotgunThreadMixin):
    """
    Shotgun shows thread, calls getShows().
    """
    def __init__(self, parent):
        super(ShotgunShowsThread, self).__init__(parent)

    def run(self):
        try:
            shows = getShows()
            self.emit(QtCore.SIGNAL('shows (PyQt_PyObject)'), shows)
        except (gaierror, getaddrinfo, getdefaulttimeout):
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), "Can't reach shotgun")
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))

class ShotgunShotsThread(QtCore.QThread, ShotgunThreadMixin):
    """
    Shotgun shots thread, calls getShots().
    """
    def __init__(self, parent, show):
        super(ShotgunShotsThread, self).__init__(parent)
        self.show = show

    def run(self):
        try:
            shots = getShots(self.show)
            self.emit(QtCore.SIGNAL('shots (PyQt_PyObject)'), shots)
        except (gaierror, getaddrinfo, getdefaulttimeout):
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), "Can't reach shotgun")
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))

class ShotgunTasksThread(QtCore.QThread, ShotgunThreadMixin):
    """
    Shotgun tasks thread, calls getTasks().
    """
    def __init__(self, parent, shot):        
        super(ShotgunTasksThread, self).__init__(parent)
        self.shot = shot

    def run(self):
        try:
            tasks = getTasks(self.shot)
            self.emit(QtCore.SIGNAL('tasks (PyQt_PyObject)'), tasks)
        except (gaierror, getaddrinfo, getdefaulttimeout):
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), "Can't reach shotgun")
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))

class ShotgunVersionsThread(QtCore.QThread, ShotgunThreadMixin):
    """
    Shotgun versions thread, calls getVersions().
    """
    def __init__(self, parent, entity, task):
        super(ShotgunVersionsThread, self).__init__(parent)
        self.entity = entity
        self.task = task

    def run(self):
        try:
            versions = getVersions(self.entity, self.task)
            self.emit(QtCore.SIGNAL('versions (PyQt_PyObject)'), versions)
        except (gaierror, getaddrinfo, getdefaulttimeout):
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), "Can't reach shotgun")
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))

class ShotgunThumbThread(QtCore.QThread, ShotgunThreadMixin):
    """
    Shotgun get thumb thread, calls getThumb().
    """
    def __init__(self, parent, entity):
        super(ShotgunThumbThread, self).__init__(parent)
        self.entity = entity

    def run(self):
        try:
            self.url = getThumb(self.entity)
            self.emit(QtCore.SIGNAL('thumbUrl (PyQt_PyObject)'), self.url)
            self.thumb = URLImage(self.url)
            self.emit(QtCore.SIGNAL('thumb (PyQt_PyObject)'), self.thumb)
        except (gaierror, getaddrinfo, getdefaulttimeout):
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), "Can't reach shotgun")
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))

class ShotgunUpdateThread(QtCore.QThread, ShotgunThreadMixin):
    """
    Shotgun entity update thread.
    """
    def __init__(self, parent, entity, params):
        super(ShotgunUpdateThread, self).__init__(parent)
        self.entity = entity
        self.params = params
        self.name = 'update'
        self.eye = params.get('eye', 'left')

    def run(self):
        self.emit(QtCore.SIGNAL('start (PyQt_PyObject)'), (self.name, self.eye))
        try:
            results = updateEntity(self.entity, params)
            self.emit(QtCore.SIGNAL('complete (PyQt_PyObject)'), results)
        except (gaierror, getaddrinfo, getdefaulttimeout):
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), "Can't reach shotgun")
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))

class MakeTakeThread(QtCore.QThread):
    """
    makeTake thread, makes a take in shotgun.
    """
    def __init__(self, parent, options):
        super(MakeTakeThread, self).__init__(parent)
        self.options = options

    def run(self):
        try:
            self.setPriority(QtCore.QThread.NormalPriority)
            self.setTerminationEnabled(True)
            results = makeTake(**self.options)
            self.emit(QtCore.SIGNAL('complete (PyQt_PyObject)'), results)
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))
            raise

class ThumbThread(QtCore.QThread):
    """
    makeThumb thread, makes a take thumbnail.
    """
    def __init__(self, parent, source, sg_take_id):
        super(ThumbThread, self).__init__(parent)
        self.source = source
        self.sg_take_id = sg_take_id

    def run(self):
        try:
            self.setPriority(QtCore.QThread.NormalPriority)
            self.setTerminationEnabled(True)
            thumb = makeThumb(self.source)
            uploadThumb(thumb, self.sg_take_id)
            self.emit(QtCore.SIGNAL('complete (PyQt_PyObject)'), thumb)
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))
            raise

class MovieThread(QtCore.QThread):
    """
    makeMov thread

    on start, emits tuple of (name, eye)
    on complete, emits results from running self.func
    """
    def __init__(self, parent, path, params):
        super(MovieThread, self).__init__(parent)
        self.name = 'movie'
        self.eye = params.get('eye', 'left')
        self.path = path
        self.params = params
        self.func = makeMov

    def isAlive(self):
        return self.isRunning()

    def run(self):
        self.emit(QtCore.SIGNAL('start (PyQt_PyObject)'), (self.name, self.eye))
        try:
            self.setPriority(QtCore.QThread.NormalPriority)
            self.setTerminationEnabled(True)
            results = self.func(self.path, **self.params)
        except Exception, e:
            self.emit(QtCore.SIGNAL('error (PyQt_PyObject)'), str(e))
            raise
        self.emit(QtCore.SIGNAL('complete (PyQt_PyObject)'), results)

class DailyThread(MovieThread):
    """
    makeDaily thread
    """
    def __init__(self, parent, path, params):
        super(DailyThread, self).__init__(parent, path, params)
        self.name = 'movie'
        self.func = makeDaily

class AvidThread(MovieThread):
    """
    makeAvid thread
    """
    def __init__(self, parent, path, params):
        super(AvidThread, self).__init__(parent, path, params)
        self.name = 'frames'
        self.func = makeAvid
