# -*- coding: utf-8 -*-
import os
import logging
import time

logger = logging.getLogger('crtsh')
logger.setLevel(logging.DEBUG)

# log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

if not os.path.exists('util/log/'):
    os.mkdir('util/log')


LOG_FILE = True
if LOG_FILE:
    fh = logging.FileHandler('util/log/crtsh.log')
    fh.setLevel( logging.DEBUG )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

# console log
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)