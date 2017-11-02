# -*- coding: utf-8 -*-

import logging
import platform
import time

from tornado.options import define, options

from util import Util

define("mode", 0, int, "Enable debug mode, 3 is network debug, 2 is debug, 1 is network release, 0 is local release")
define("port", 5505, int, "Listen port")
define("address", "0.0.0.0", str, "Bind address")
if platform.system() == 'Windows':
    default_log_file = 'D:/log/oa.log'
else:
    default_log_file = '/data/log/oa/oa.log'
define('log_file', default_log_file, str, 'log file')
define('log_level', 'info', str, 'log level')
options.parse_command_line()
log_level = options.log_level.lower()
if log_level == 'debug':
    log_level = logging.DEBUG
elif log_level == 'warning':
    log_level = logging.WARNING
elif log_level == 'error':
    log_level = logging.ERROR
else:
    log_level = logging.INFO
Util.init_logging(options.log_file, log_level)

if __name__ == '__main__':

    # 测试在200s内创建文件多个日志文件
    for i in range(0, 10):
        logging.debug("logging.debug")
        logging.info("logging.info")
        logging.warning("logging.warning")
        logging.error("logging.error")
        time.sleep(2)