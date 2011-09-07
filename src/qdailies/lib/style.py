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
BASE = os.path.join(os.path.dirname(__file__))

d = {
    'gfx' : os.path.join(BASE, '..', 'gfx')
}

scrollbar = """
QScrollBar:vertical {
    border: 0px;
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #272727, stop: 1.0 #3b3b3b);
    width: 13px;
    margin-top: 18px;
    margin-bottom: 18px;
}
QScrollBar::handle:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                  stop: 0 #a4a4a4, stop: 0.4 #999999,
                                  stop: 0.5 #999999, stop: 1.0 #a4a4a4);

    min-height: 12px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #6c6c6c, stop: 1.0 #464646);
    width: 13px;
    height: 18px;
    border: 0px;
    subcontrol-position: bottom right;
    subcontrol-origin: margin;
}
QScrollBar::sub-line:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #6c6c6c, stop: 1.0 #464646);
    width: 13px;
    height: 18px;
    border: 0px;
    subcontrol-position: top right;
    subcontrol-origin: margin;
    position: absolute;
    bottom: 20px;
}
QScrollBar:up-arrow:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #6c6c6c, stop: 1.0 #464646);
    image: url(%(gfx)s/icon.sb.up.png);
    width: 8px;
}
QScrollBar::down-arrow:vertical {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #6c6c6c, stop: 1.0 #464646);
    image: url(%(gfx)s/icon.sb.down.png);
    width: 8px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
""" % d

tree = """
QGroupBox {
    border: 0px;
    margin: 0px;
    padding: 0px;
}
QHeaderView::section {
    background-image: none;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #aaa, stop: 1.0 #868686);
    color: #111;
    font-weight: bold;
    font-size: 11px;
    font-family: Arial;
    padding-left: 5px;
    border-top: 1px solid #c9c9c9;
    border-right: 1px solid #5e5e5e;
    border-left: 1px solid #a9a9a9;
    border-bottom: 0px solid #282828;
    height: 17px;
    margin: 0px;
}
QTreeView {
    background-color: #373737;
    alternate-background-color: #313131;
    border: 0px;
}
QTreeView::branch {
    width: 0px;
}
QTreeView::item {
    color: #dddddd;
    border-bottom: 1px solid #333;
    border-right-color: transparent;
    border-top-color: transparent;
    height: 20px;
}
QTreeView::item:selected {
    background: #273;
}
QTreeView::indicator {
    padding-left: -9px;
}
QTreeView::indicator:checked {
    image: url("%(gfx)s/icon.checked.png");
}
QTreeView::indicator:unchecked {
    image: url("%(gfx)s/icon.unchecked.png");
}
QTreeView:disabled {
    background-image: url(%(gfx)s/loading.png);
    background-repeat:no-repeat;
    background-attachment:fixed;
    background-position:center;
}
""" % d

dock = """
QDockWidget {
    border: 1px solid #292929;
    border-top: 0px;
    titlebar-close-icon: url(%(gfx)s/close.png);
    titlebar-normal-icon: url(%(gfx)s/undock.png);
}
QDockWidget::title {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #acacac, stop: 1.0 #979797);
    border-bottom: 1px solid #292929;
    border-top: 0px;
    text-align: left;
    color: #707070;
    padding-left: 5px;
    height: 24px;
}
""" % d

toolbar = """
QToolBar {
    border: 0px;
}
""" % d

main = """
QMainWindow::separator {
    background: #555;
    width: 4px;
    height: 4px;
}
QMainWindow::separator:hover {
    background: #3a3;
}
""" % d

searchbar = """
#background {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #a0a0a0, stop: 1.0 #828282);
    border-bottom: 1px solid #363636;
    border-top: 0px;
}
QGroupBox {
    border: 0px;
    margin: 0px;
    padding: 0px;
}
QLineEdit {
    background: #eee;
    border: 1px solid #5e5e5e;
    border-right: 0px;
    border-left: 0px;
    padding-left: 0px;
    color: #222;
}
#btnSearch, #showCombo {
    background: #eee;
    background-image: url(%(gfx)s/icon.search.png);
    border: 1px solid #5e5e5e;
    border-right: 0px;
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
}
#btnClear {
    background: #eee;
    border: 1px solid #5e5e5e;
    border-left: 0px;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}
#btnNew {
    background-image: url(%(gfx)s/icon.new.png);
    border: 0px;
}
QComboBox::drop-down {
    border-width: 0px;
}
QComboBox::down-arrow {
    image: url(noimg);
    border-width: 0px;
}
QComboBox:on {
    padding-top: 3px;
    padding-left: 4px;
}
QComboBox:editable {
    width: 0px;
}
QComboBox QAbstractItemView {
    background: #eee;
    color: #111;
    selection-background-color: #1a1;
    border: 0px;
}
""" % d

controlbar = """
#background {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #4d4d4d, stop: 1.0 #3d3d3d);
    border-top: 1px solid #656565;
    border-bottom: 1px solid #363636;
}
QLabel {
    color: #efefff;
    font-size: 10px;
    font-family: verdana;
}
#btnPlay {
    background-image: url(%(gfx)s/icon.btn.play.png);
    background-repeat: none;
    width: 31px;
    height: 33px;
    border: 0px;
}
#btnPlay:disabled {
    background-image: url(%(gfx)s/icon.btn.play.off.png);
}
#btnNext {
    background-image: url(%(gfx)s/icon.btn.next.png);
    background-repeat: none;
    width: 25px;
    height: 25px;
    border: 0px;
}
#btnNext:disabled {
    background-image: url(%(gfx)s/icon.btn.next.off.png);
}
#btnPrev {
    background-image: url(%(gfx)s/icon.btn.prev.png);
    background-repeat: none;
    width: 25px;
    height: 25px;
    border: 0px;
}
#btnPrev:disabled {
    background-image: url(%(gfx)s/icon.btn.prev.off.png);
}
#volumeLabel {
    background-image: url(%(gfx)s/icon.volume.png);
    background-repeat: none;
    width: 13px;
    height: 25px;
    border: 0px;
}
QSlider::groove:horizontal {
    background-image: none;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #101010, stop: 1.0 #2b2b2b);
    border-top: 1px solid #505050;
    border-bottom: 1px solid #101010;
    border-radius: 5px;
    margin: 2px 0;
    height: 10px;
}
QSlider::handle:horizontal {
    background-image: none;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #e2e2e2, stop: 1.0 #8c8c8c);
    border-top: 1px solid #ededed;
    border-radius: 5px;
    width: 10px;
    height: 10px;
}
QSlider::sub-page:horizontal {
    background-image: none;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #2b2b2b, stop: 1.0 #101010);
    border-top: 1px solid #505050;
    border-bottom: 1px solid #101010;
    border-radius: 5px;
    margin: 2px 0;
    height: 10px;
}
""" % d

new = """
* {
    background: #2c2f32;
}
QGroupBox {
    background: #555;
    border: 0px;
}
QTabWidget {
    background: #555;
    border: 0px;
}
#seqBox {
    background: #555;
}
#submitBox {
    background: #4a4a4a;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #444, stop: 1.0 #333438);
}
#dailiesBox {
    background: #555;
}
#optionsBox {
    border-left: 1px solid #555;
}
QLabel, QCheckBox {
    padding-left: 5px;
}
QLineEdit, #scaleCombo, #avidCombo {
    height: 25px;
    border: 0px;
    border-radius: 0px;
    background: #333;
    color: #4a4;
    font-family: helvetica, arial;
}
#comment {
    color: #aaa;
    font-family: arial, verdana;
}
#leftEdit, #rightEdit {
    background: #444;
    color: #999;
    border: #0;
    border-left: 1px solid #555;
}
#cropBox QLineEdit {
    color: #aa4;
}
QDialog, QComboBox, QCheckBox, QLabel {
    background: #3a3a3a;
    color: #999;
    border: 0px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border: 0px;
}
QComboBox::down-arrow {
    image: url(%(gfx)s/icon_arrow_down.png);
}
QComboBox QAbstractItemView {
    background: #333;
    color: #aaa;
    border: 0px solid darkgray;
    selection-background-color: #5a5;
}
QHeaderView::section {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #444549, stop: 1.0 #333438);
    color: #888;
    padding-left: 5px;
    border: 0px solid #6a6d70;
    border-right: 1px solid #555;
    border-bottom: 1px solid #555;
    height: 25px;
}
QTreeWidget {
    background-color: #222325;
    /*background-image: url(%(gfx)s/tree.png);*/
    background-repeat: repeat-x;
    background-attachment: fixed;
    border: 0px;
}
QTreeView::item {
    background: #222427;
    color: #888;
    border-bottom: 1px solid #333;
    border-right-color: transparent;
    border-top-color: transparent;
}
QTreeView::item:selected {
    background: #34b;
}
QLineEdit:disabled, QCheckBox:disabled, QLabel:disabled, QComboBox:disabled {
    background: #454545;
    color: #222;
}
QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #444, stop: 1.0 #333438);
    border: 1px solid #333;
    font-family: verdana;
    font-size: 10px;
    color: #aaa;
    width: 80px;
    height: 25px;
}
#btnSubmit {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #444, stop: 1.0 #333438);
    border: 1px solid #222;
    border-radius: 2px;
    fond-weight: bold;
}
#btnCancel {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #444, stop: 1.0 #333438);
    border: 1px solid #292929;
    border-radius: 2px;
    color: #999;
}
#btnToggleOut1, #btnToggleOut2 {
    background: #444;
    image: url(%(gfx)s/icon.save.png);
    border: 0px;
    border-left: 1px solid #555;
}
QSlider::groove:horizontal {
    height: 25px;
    border-left: 1px solid #555;
    border-top: 1px solid #555;
    margin: 2px 0;
    background-image: url(%(gfx)s/slider.png);
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #444, stop: 1.0 #444);
}
QSlider::handle:horizontal {
    background-image: url(%(gfx)s/slider-handle.png);
    background-repeat: none;
    background-position: left;
    width: 12px;
    height: 25px;
}
QProgressBar {
    border: 0px;
    background: #353535;
}
QProgressBar::chunk {
    border: 0px;
    background-color: #242628;
    background-image: url(%(gfx)s/progress.png);
}
QSpinBox {
    border: 0px;
    background: #333;
    color: #aaa;
}
QSpinBox::up-button, QSpinBox::down-button {
    border: 1px solid #333;
    background: #444;
}
#outputBox QComboBox,
#outputBox QLineEdit {
    background: #333;
    border-left: 1px solid #555;
}
""" % d
