# -*- coding: utf-8 -*-

import logging, logging.handlers
import platform

class Util:

    @staticmethod
    def initialize(**kwargs):
        pass

    @staticmethod
    def init_logging(target='temp.log', level=logging.DEBUG):
        reload(logging)
        reload(logging.handlers)
        format = "%(asctime)s [%(levelname)s] [%(filename)s line:%(lineno)d] %(message)s\n"
        datefmt = '%Y-%m-%d %H:%M:%S'
        _config = {
            'format': format,
            'datefmt': datefmt,
            'level': level,
        }
        if platform.system().lower() == 'linux':
            _config['filename'] = target
        logging.basicConfig(**_config)
        if '.' in target:
            target = target[:target.rindex('.')]
        fileshandle = logging.handlers.TimedRotatingFileHandler('%s__' % target, when='midnight', interval=1)
        fileshandle.suffix = "%Y_%m_%d_%H_%M_%S.log"
        fileshandle.setLevel(level)
        formatter = logging.Formatter(format)
        formatter.datefmt = '%Y-%m-%d %H:%M:%S'
        fileshandle.setFormatter(formatter)
        logging.getLogger('').addHandler(fileshandle)