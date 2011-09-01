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

# ---------------------------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------------------------
BASE = os.path.join(os.path.dirname(__file__))
UI_ROOT = os.path.join(BASE, '..', 'ui')
GFX_ROOT = os.path.join(BASE, '..', 'gfx')
WIDGET_ROOT = os.path.join(BASE, '..', 'widgets')
PREFS_ROOT = os.path.join(BASE, '..', 'prefs')

LOG_ROOT = '/tmp/log'

ROOTS = {
    'win32': '\\\\unc\\path',
    'linux': '/tmp',
    'darwin': '/tmp',
}

# root paths
ROOT = ROOTS.get(sys.platform, '/tmp')
LOG_ROOT = os.path.join(ROOT, 'log')
DAILIES_ROOT = os.path.join(ROOT, 'show')
HOMEDIR = os.environ.get('HOME')
DEFAULT_THUMB = os.path.join(GFX_ROOT, 'icon_thumb.png')

# output movie path template
DAILIES_MOVIE_PATH = os.path.join(DAILIES_ROOT,
    '%(show)s', '%(sequence)s', '%(shot)s', 'all_movies',
    '%(shot)s_%(task)s_%(version)s_%(eye)s.mov'
    )

# output avid path template
DAILIES_AVID_PATH = os.path.join(DAILIES_ROOT,
    '%(show)s', '%(sequence)s','%(shot)s', 'elem', 'hd', '%(version)s', '%(eye)s',
    '%(shot)s_%(task)s_%(version)s_%(eye)s.#.jpg'
    )

# dailies take name template
DAILIES_TAKE_NAME = '%(shot)s_%(task)s_tk%(version)s'

# ---------------------------------------------------------------------------------------------
# RV
# ---------------------------------------------------------------------------------------------
RV_SLATE_TITLE = 'SHADEMAKER'
RV_SEQ_FORMAT = '%h%p%t %r' # pyseq string formatting
RV_PADDING = 4
RV_WIDTH = 720
RV_QUALITY = 1.00
RV_CROP = (0, 270, 5183, 3186)
RV_FRAMES_WIDTH = 1080
RV_FRAMES_QUALITY = 1.00
RV_SCALE_OPTIONS = {
    'qvga': (320, 240),
    'vga': (640, 480),
    'svga': (800, 600),
    'hd480': (852, 480),
    'hd720': (1280, 720),
    'hd1080': (1920, 1080),
}
RV_RVIO_OPT = [ '-insrgb', '-outsrgb', '-rthreads 4', ]
RV_PATHS = {
    'darwin': '/Applications/RV64.app/Contents/MacOS/RV64',
    'linux': 'rv',
    'win32': 'C:\\\\Program Files\\Tweak\\rv.exe',
}
RVIO_PATHS = {
    'darwin': '/Applications/RV64.app/Contents/MacOS/rvio' ,
    'linux': 'rvio',
    'win32': 'C:\\\\Program Files\\Tweak\\rvio.exe',
}
RV_PATH = RV_PATHS.get(sys.platform, 'rv')
RV_RVIO_PATH = RVIO_PATHS.get(sys.platform, 'rvio')
RV_STEREO_MODE = 'anaglyph'

# ---------------------------------------------------------------------------------------------
# SHOTGUN
# ---------------------------------------------------------------------------------------------
SG_SCRIPT_URL = 'https://shademaker.shotgunstudio.com'
SG_SCRIPT_NAME = 'dailies_tool'
SG_SCRIPT_KEY = '7b655b6b85855d659bf4ffd6d0df05e1e8467cd0'
# shotgun field names may vary, so create a map
SG_FIELD_MAP = {
    'ID': 'id',
    'NAME': 'code',
    'TASK': 'content',
    'SHOW': 'sg_short_name',
    'COMMENT': 'description',
    'DATE_CREATED': 'created_at',
    'TAKE_NUMBER': 'sg_take__',
    'FRAMES_LEFT': 'sg_path_to_frames_left',
    'FRAMES_RIGHT': 'sg_path_to_frames_right',
    'MOVIE_LEFT': 'sg_path_to_movie_left',
    'MOVIE_RIGHT': 'sg_path_to_movie_right',
    'STATUS': 'sg_status_list',
}

# ---------------------------------------------------------------------------------------------
# STYLE
# ---------------------------------------------------------------------------------------------
STATUS_COLOR_MAP = {
 'rev' : (50, 100, 50),
 'ip' : (50, 50, 200),
 'rej' : (150, 50, 50),
 'na' : (100, 100, 100),
 'vwd' : (50, 50, 50),
 'cmpt' : (50, 200, 50),
 'apr' : (50, 200, 50),
 'default' : (50, 50, 50)
}
