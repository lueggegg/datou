import mysql_inst_mgr

class MySQLConfig:
    def __init__(self, *args, **kwargs):
        host = '127.0.0.1'
        port = 3306
        passwd = '123456'
        db = 'debug_oa'
        if 'mode' in kwargs and kwargs['mode'] == 1:
            host = '203.88.48.251'
            port = 13306
        self.global_metas = (mysql_inst_mgr.DBMeta(host=host, port=port, user='root', passwd=passwd, db=db),)