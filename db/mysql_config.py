import mysql_inst_mgr
import platform

class MySQLConfig:
    def __init__(self, *args, **kwargs):
        host = '127.0.0.1'
        port = 3306
        passwd = '123456'
        if platform.system() == 'Windows':
            db = 'release_oa_bk_1'
        else:
            db = 'release_oa'
        if 'mode' in kwargs:
            if kwargs['mode'] == 1:
                host = '203.88.48.251'
                port = 13306
            elif kwargs['mode'] == 2:
                db = 'debug_oa'
            elif kwargs['mode'] == 3:
                host = '203.88.48.251'
                port = 13306
                db = 'debug_oa'
        self.global_metas = (mysql_inst_mgr.DBMeta(host=host, port=port, user='root', passwd=passwd, db=db),)