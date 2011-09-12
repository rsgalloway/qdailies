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
import traceback
from glob import glob
from datetime import datetime

from pyseq import Sequence, uncompress

from qdailies.lib.sglib import getShows, getShots, getTasks, getVersions, updateEntity
from qdailies.lib.logger import log
from qdailies.lib import config

__all__ = ['makeDaily', 'makeAvid', 'makeThumb', 'makeMov', 'makeTake', ]

# ---------------------------------------------------------------------------------------------
# RV LEADER EXAMPLE
# ---------------------------------------------------------------------------------------------
"""
simpleslate: side-text Field1=Value1 Field2=Value2 ...
watermark: text opacity
frameburn: opacity grey font-point-size
bug: file.tif opacity scale
matte: aspect-ratio opacity

Movie w/Slate:        rvio in.#.jpg -o out.mov -leader simpleslate "FilmCo" \
                             "Artist=Jane Q. Artiste" "Shot=S01" "Show=BlockBuster" \
                             "Comments=You said it was too blue so I made it red"
Movie w/Watermark:    rvio in.#.jpg -o out.mov -overlay watermark "FilmCo Eyes Only" .25
Movie w/Frame Burn:   rvio in.#.jpg -o out.mov -overlay frameburn .4 1.0 30.0
Movie w/Bug:          rvio in.#.jpg -o out.mov -overlay bug logo.tif .3 .5
Movie w/Matte:        rvio in.#.jpg -o out.mov -overlay matte 2.35 0.8
Multiple:             rvio ... -leader ... -overlay ... -overlay ...
"""

def makeTake(show, shot, **kwargs):
    """
    Creates the Version/Dailies entity in Shotgun.

    :param show: Project short name (sg_short_name)
    :param shot: Shot code (code)
    :param kwargs: Valid kwargs are

        name: Name of the take, must be unique
        comment: Dailies comments
        version: Dailies take, pts or version number
        leftMoviePath: Left-eye (or mono) movie file path
        leftFramesPath: Left-eye (or mono) frames file path
        rightMoviePath: Right-eye movie file path
        rightFramesPath: Right-eye frames file path

    :return: Shotgun entity dict
    :raise: shotgun.Fault
    """

    try:
        from shotgun import Shotgun
        sg = Shotgun(config.SG_SCRIPT_URL, config.SG_SCRIPT_NAME, config.SG_SCRIPT_KEY)
    except ImportError:
        raise Exception('error importing shotgun api')

    log.debug('makeTake: %s' % kwargs)

    # get show and shot from shotgun
    _show = getShows(show)[0]
    _shot = getShots(show, shot)[0]
    _task = None

    # look for task
    results = getTasks(_shot, kwargs.get('task'))
    if results:
        _task = results[0]

    # take version number
    version = kwargs.get('version')
    if not version:
        version = len(getVersions(_shot, _task)) + 1
        kwargs.update(version=version)

    # take name
    _name = {
        'show': show,
        'shot': shot,
        'sequence': shot.split('_')[0],
        'task': kwargs.get('task', ''),
        'version': version,
        'eye': kwargs.get('eye', ''),
    }
    name = kwargs.get('name', config.DAILIES_TAKE_NAME % _name)

    # basic required fields
    params = {
        'entity': _shot,
        'project': _show,
        config.SG_FIELD_MAP.get('NAME'): name,
        config.SG_FIELD_MAP.get('COMMENT'): kwargs.get('comment', ''),
        config.SG_FIELD_MAP.get('TAKE_NUMBER'): str(version),
    }

    # shotgun task
    if _task:
        params.update(**{'sg_task': _task})

    # file paths
    leftMoviePath = kwargs.get('leftMoviePath')
    leftFramesPath = kwargs.get('leftFramesPath')
    rightMoviePath = kwargs.get('rightMoviePath')
    rightFramesPath = kwargs.get('rightFramesPath')

    # link to left-eye movie/frames
    if leftMoviePath:
        params.update(**{config.SG_FIELD_MAP.get('MOVIE_LEFT'): leftMoviePath})
    if leftFramesPath:
        params.update(**{config.SG_FIELD_MAP.get('FRAMES_LEFT'): leftFramesPath})

    # link to right-eye movie/frames
    if rightMoviePath:
        params.update(**{config.SG_FIELD_MAP.get('MOVIE_RIGHT'): rightMoviePath})
    if rightFramesPath:
        params.update(**{config.SG_FIELD_MAP.get('FRAMES_RIGHT'): rightFramesPath})

    sg_take = sg.create('Version', params)

    return sg_take

def makeThumb(source, frame=2, res=256):
    """
    Creates png thumbnail from the source.

    :param source: rvio source input (movie, sequence)
    :param frame: frame to create thumbnail from
    :param res: thumbnail width in pixels

    :return: thumbnail path
    """
    import tempfile
    thumb = tempfile.mkstemp(prefix='thb', suffix='.png')[1]
    cmd = "%s %s -resize %d -t %d -o %s" % (config.RV_RVIO_PATH, source, res, frame, thumb)
    log.debug('makeThumb: %s' % cmd)
    os.system(cmd)
    return thumb

def makeAvid(frames, **kwargs):
    log.debug('makeAvid: %s' % kwargs)
    return makeMov(frames, **kwargs)

def makeDaily(frames, **kwargs):
    log.debug('makeDaily: %s' % kwargs)
    return makeMov(frames, **kwargs)

def makeMov(frames, **kwargs):
    """
    Makes a movie file from a frame sequence.

    :param sequences: rvio-compatible file sequence string

    :param kwargs: Supported kwargs

        show         shotgun show name
        shot         shotgun shot code
        task         shotgun task name
        version      version or pts number*
        width        width of mov to resize [0 (same as input)]
        quality      compression quality 0 to 1.0 [0.95]
        outfile      output movie file path
        dailies      submit this movie to shotgun (bool)*
        comment      slate comment and take description
        frameBurn    burn frame numbers into frames (bool)

    * If dailies is true, all kwargs get passed to makeTake.
    * If version is None, a version number will be auto generated.

    :return: path to generated movie file
    """
    _in = frames
    _out = kwargs.get('outfile', config.DAILIES_MOVIE_PATH % kwargs)

    # slate settings
    _show = kwargs.get('show', None)
    _shot = kwargs.get('shot', None)
    _task = kwargs.get('task', None)
    _slate = kwargs.get('slate', False)
    _user = kwargs.get('user', os.environ.get('USER'))
    _date = time.strftime('%a %b %e, %Y %l:%M%P')
    _comment = kwargs.get('comment', '')

    # rvio settings
    _width = kwargs.get('width', config.RV_WIDTH)
    _height = kwargs.get('height', None)
    _crop = kwargs.get('crop', None)
    _resize = kwargs.get('resize', None)
    _quality = kwargs.get('quality', config.RV_QUALITY)
    _frameBurn = kwargs.get('frameBurn', False)
    _dryRun = kwargs.get('dryRun', False)

    # rvio options strings
    perSeqOpts = []
    optionStrings = config.RV_RVIO_OPT[:]

    # scale / resize / crop
    if _height:
        optionStrings.append('-outres %d %d' %(_width, _height))
    else:
        optionStrings.append('-resize %d' % _width)

    if _resize and type(_resize) in (list, tuple):
        optionStrings.append('-resize "%d %d"' %(_resize[0], _resize[1]))

    if _crop and type(_crop) in (list, tuple):
        perSeqOpts.append('-crop %d %d %d %d' %(_crop[0], _crop[1], _crop[2], _crop[3]))

    # quality
    optionStrings.append('-quality %s' % _quality)
    optionStrings.append('-v')

    # rvio slate options
    if _slate:
        slateArgs = ['-leader', 'simpleslate', config.RV_SLATE_TITLE, ]
        slateArgs.append('"Show=%s"' % _show)
        slateArgs.append('"Shot=%s"' % _shot)
        slateArgs.append('"Task=%s"' % _task)
        slateArgs.append('"Date=%s"' % _date)
        slateArgs.append('"User=%s"' % _user)
        slateArgs.append('"Source=%s"' % _in)
        slateArgs.append('"Comments=%s"' % _comment)
        optionStrings.extend(slateArgs)

        if _frameBurn:
            optionStrings.extend(['-overlay', 'frameburn', '0.5', '0.5', '20.0', ])

    # the command string
    cmd = "%s [ %s %s ] %s -o %s" % (config.RV_RVIO_PATH, _in, ' '.join(perSeqOpts), ' '.join(optionStrings), _out)
    log.debug('cmd: %s' % cmd)

    # check to make sure base dir exists
    _basedir = os.path.dirname(_out)
    if not os.path.isdir(_basedir):
        try:
            os.makedirs(_basedir)
        except EnvironmentError, e:
            log.error(traceback.format_exc())
            if not os.path.exists(_basedir):
                return

    # execute the command
    if _dryRun:
        log.info(cmd)
    else:
        os.system(cmd)

    return _out

def main(args):
    """
    Creates daily.

    :param args: ArgParse args object.
    """
    left = None
    right = None

    # options dict for makeMov
    options = dict(
        quality = args.quality,
    )

    # list of file sequences
    seqs = []
    for seq in args.inputSeq:
        seqs.append(seq)

    # validate args, build options
    if args.quality < 0.0 or args.quality > 1.0:
        raise Exception("quality must be between 0.0 and 1.0")
    if args.dailies:
        options.update(dailies=True)
    if args.outputMov and not args.outputMov.endswith('.mov'):
        raise Exception("output movie file must end with '.mov'")

    # set options
    if args.width > 0:
        options.update(width=args.width)
    if args.dryRun:
        options.update(dryRun=True)
    if args.frameBurn:
        options.update(frameBurn=True)
    if args.comment:
        options.update(slate=True, comment=args.comment)
    if args.outputMov:
        options.update(outfile=args.outputMov)
    if args.dailies:
        options.update(status='rev')

    # create shotgun version
    sg_version_dict = makeTake(**dict(options, **{'eye': 'left'}))
    options.update(version=sg_version_dict.get(config.SG_FIELD_MAP.get('TAKE_NUMBER')))

    # make the left-eye/mono movie
    left = makeMov(seq, **options)

    # make the right-eye movie
    if args.stereo:
        right = makeMov(args.stereo, **dict(options, **{'eye': 'right'}))

    # update shotgun with file paths
    params = {
        config.SG_FIELD_MAP.get('FRAMES_LEFT'): seq,
        config.SG_FIELD_MAP.get('FRAMES_RIGHT'): args.stereo,
        config.SG_FIELD_MAP.get('MOVIE_LEFT'): left,
        config.SG_FIELD_MAP.get('MOVIE_RIGHT'): right,
    }
    updateEntity(sg_version_dict, params)

    # play in rv
    if args.runRv and not args.dryRun:
        if left and right:
            os.system('%s [ %s %s ] -stereo %s' %(config.RV_PATH, left, right, config.RV_STEREO_MODE))
        else:
            os.system('%s %s' %(config.RV_PATH, left))

    return (0)

def process_args():
    """
    Builds options dict.

    :return: ArgParse args object.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="dailies",
        description="""
            Make a movie file from sequences of images and
            optionally submit to shotgun for dailies review.
        """,
        epilog="""
        """,
    )

    # dry-run
    parser.add_argument('-d',
                dest='dryRun', action='store_true', default=False,
                help='just print rvio command only')

    # input options
    input_group = parser.add_argument_group('Input',
                'Input file sequences separated by spaces')
    input_group.add_argument('inputSeq',
                action='store', type=str, metavar='input',
                help='list of input file sequences, e.g. name.1001-1100.dpx')
    input_group.add_argument('--show',
                dest='show', action='store', required=False, type=str, default=os.environ.get('SHOW', ''),
                help='show name')
    input_group.add_argument('--shot',
                dest='shot', action='store', required=False, type=str, default=os.environ.get('SHOT', ''),
                help='shot name')
    input_group.add_argument('--task',
                dest='task', action='store', required=False, type=str, default=os.environ.get('TASK', ''),
                help='task name')
    input_group.add_argument('--rev',
                dest='version', action='store', required=False, type=str, default=None,
                help='version or pts number')

    # output options
    output_group = parser.add_argument_group('Output',
                'Output movie will be out.mov unless -o option used')
    output_group.add_argument('-o',
                dest='outputMov', action='store', type=str, default=None,
                help='path of output movie')
    output_group.add_argument('-R',
                dest='runRv', action='store_true', default=False,
                help='run rv on the output movie')

    # misc options
    option_group = parser.add_argument_group('Options',
                'Options passed to rvio command')
    option_group.add_argument('-q',
                dest='quality', action='store', required=False, type=float, default=config.RV_QUALITY, 
                help='compression quality, 0: low, 1.0: high')
    option_group.add_argument('-w', 
                dest='width', action='store', required=False, type=int, default=config.RV_WIDTH,
                help='resize movie to width')
    option_group.add_argument('--frames', 
                dest='frameBurn', action='store_true', default=False,
                help='burn frame numbers')
    option_group.add_argument('-c', 
                dest='comment', action='store', type=str, default='', 
                help='slate the movie and add comment')
    option_group.add_argument('--stereo', 
                dest='stereo', action='store', default=False,
                help='right-eye sequence, creates right-eye movie')
    option_group.add_argument('-D', 
                dest='dailies', action='store_true', default=False,
                help='submit to shotgun (requires show and shot pre-set)')

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    try:
        args = process_args()
        sys.exit(main(args))
    except Exception, e:
        print e
    except KeyboardInterrupt:
        print 'Stopping...'
        sys.exit(1)
