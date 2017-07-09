import mysql_inst_mgr

class MySQLConfig:
    def __init__(self, *args, **kwargs):
        self.global_metas = (mysql_inst_mgr.DBMeta(host='127.0.0.1', port=3306, user='root', passwd='123456', db='tv_oa'),)