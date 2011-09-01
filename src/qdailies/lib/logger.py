#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Enluminari, Inc. (http://www.enluminari.com)
#

import os
import logging
from datetime import datetime
import config

log = logging.Logger('dailies')
log.setLevel(logging.DEBUG)

# stdout
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(streamHandler)

# log file
now = datetime.now()
date = '%04d-%02d-%02d' %(now.year, now.month, now.day)
_log_dir = os.path.join(config.LOG_ROOT, date)
if not os.path.isdir(_log_dir):
    try:
        os.makedirs(_log_dir)
    except EnvironmentError, e:
        log.debug('Could not create log dir: %s\n%s' % (_log_dir, e))
fileHandler = logging.FileHandler(os.path.join(_log_dir, 'dailies.log'))
fileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(fileHandler)
