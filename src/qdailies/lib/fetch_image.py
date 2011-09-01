#!/bin/env/python

import os
import sys
import traceback
from urllib import urlopen

from PyQt4 import QtGui
from PyQt4 import QtCore

BASEDIR = os.path.dirname(os.path.realpath(__file__))

def fetchURL(url):
    local=""
    type="text"
    subtype="plain"
    try:
        remote=urlopen(url)
        info=remote.info()
        (type,subtype)=info.gettype().split("/")
        local=remote.read()
        l=info.getheader('content-length')
        if not l:
            l=0
        else:
            l=int(l)

        p=0
        c=0
        bsize=1024
        while True:

            c=c+1
            buf=remote.read(int(bsize))

            #End of file
            if buf=='':
                break

            p=p+len(buf)
            local=local+buf

    except:
        traceback.print_exc()
    return (local,type,subtype)

class URLImage(QtGui.QImage):
    def __init__(self, url):
        QtGui.QImage.__init__(self)
        self.isDefault = False
        self.url = url
        if url:
            img_data, imtype, subtype = fetchURL(str(url))
            try:
                self.byte_array = QtCore.QByteArray(img_data)
                if not self.loadFromData(self.byte_array, None):
                    print 'Error loading image from url', url
            except Exception, e:
                print 'Error loading image from url', url, e
                self.loadDefault()
        else:
            self.loadDefault()

    def loadDefault(self):
        self.isDefault = True
        default_path = os.path.join(BASEDIR, 'movie_clip.png')
        self.load(default_path)

    def asPixmap(self):
        pixmap = QtGui.QPixmap(QtCore.QVariant(self))
        pixmap.fromImage(self)
        return pixmap

    def asIcon(self):
        return QtGui.QIcon(self.asPixmap())
