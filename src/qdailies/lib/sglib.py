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

from pyseq import getSequences

from qdailies.lib.fetch_image import URLImage
from qdailies.lib import config
from qdailies.lib.logger import log

try:
    from shotgun import Shotgun
    sg = Shotgun(config.SG_SCRIPT_URL, config.SG_SCRIPT_NAME, config.SG_SCRIPT_KEY)
except ImportError:
    raise Exception('error importing shotgun api')

def getShows(show=None):
    """
    Gets a list of shows from shotgun.

    :param show: show short name

    :return: project list from shotgun

    :raise: gaierror if can't connect to shotgun.
    """
    if show is None:
        params = []
    else:
        params = [['sg_short_name', 'is', show]]
    try:
        return sg.find('Project', params, fields=['name', 'sg_short_name'])
    except gaierror, e:
        raise

def getShots(show, code=None):
    """
    Gets a list of shots from shotgun given a project dictionary.

    :param show: Show short name or shotgun show dict

    :return: shot list from shotgun for given project

    :raise: gaierror if can't connect to shotgun.
    """
    if type(show) != dict:
        results = getShows(show)
        if results:
            show = results[0]
    params = [['project', 'is', show]]
    if code is not None:
        params.append([config.SG_FIELD_MAP.get('NAME'), 'is', code])
    try:
        return sg.find('Shot', params, fields=[config.SG_FIELD_MAP.get('NAME')])
    except gaierror, e:
        raise

def getTasks(entity, content=None):
    """
    Gets a list of tasks from shotgun given a shot dictionary.

    :param entity: sg entity dict
    :param content: sg task name

    :return: list of tasks from shotgun

    :raise: gaierror if can't connect to shotgun.
    """
    params = [['entity', 'is', entity]]
    if content is not None:
        params.append(['content', 'is', content])
    try:
        return sg.find('Task', params, fields=['content'])
    except gaierror, e:
        raise

def getVersions(entity, task=None):
    """
    Gets a list of versions from shotgun given a shot and task dictionary.

    :param entity: shotgun entity dict
    ;param task: shotgun task dict or content string

    :return: version list from shotgun for given shot and task

    :raise: gaierror if can't connect to shotgun.
    """
    assert type(entity) == dict, 'invalid entity dict in getVersions'

    params = [['entity', 'is', entity]]

    if task:
        if type(task) != dict:
            results = getTasks(entity, task)
            if results:
                task = results[0]

        params.append(['sg_task', 'is', task])

    # get shotgun versions
    try:
        log.debug('find versions: %s' % params)
        versions = sg.find('Version', params, fields=config.SG_FIELD_MAP.values())
    except gaierror, e:
        raise

    return versions

def getThumb(entity):
    """
    Get thumbnails from shotgun.

    :param entity: shotgun entity dict.
    """
    try:
        url = sg._get_thumb_url('Version', entity.get('id'))
    except:
        log.warning('Error getting image for %s' % entity.get('id', ''))
        url = None
    return url

def getSequence(fileName):
    """
    Find sequences in the parent folder of fileName and return the 
    sequence to which fileName belongs.

    :param fileName: file path.

    :return: pyseq.Sequence instance.
    """
    dirName = os.path.dirname(fileName)
    files = [os.path.join(dirName, f) for f in os.listdir(dirName)]
    seqs = getSequences(files)
    for seq in seqs:
        if seq.contains(fileName):
            return seq

def updateEntity(entity, params):
    """
    Updates a shotgun entity with params.

    :param entity: shotgun entity dict
    :param params: key/value pairs
    """
    return sg.update(entity.get('type'), entity.get('id'), params)

def uploadThumb(thumb, sg_take_id):
    """
    Uploads thumb to shotgun.

    :param thumb: path to thumbnail
    :param sg_take_id: shotgun take id
    """
    sg.upload_thumbnail('version', sg_take_id, thumb)

