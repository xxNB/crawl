# -*- coding: utf-8 -*-
import logzero
import logging
import os
from logzero import logger

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logzero.formatter(formatter)
file_path = os.path.join(os.path.dirname(__file__), 'error.log')
logzero.logfile(filename=file_path, loglevel=logging.ERROR)

if __name__ == '__main__':
    logger.info('info')
    logger.debug('debug')
    logger.error('error')
    # import os
    print(os.path.dirname(__file__))