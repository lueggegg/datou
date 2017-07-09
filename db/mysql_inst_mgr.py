# -*- coding: utf-8 -*-

import logging
import random

import mysql_pool


class DBMetaException(Exception):
    def __init__(self, message):
        self._message = message  
    
    def __str__(self):
        return self._message 
    
class DBMeta:
    def __init__(self, *args, **kwargs):
        self.slice_range = None                 # Data slice hash range, like(0, 100) means 0 >= range <= 100
        self.host = "localhost"                 # DB host 
        self.port = 3306                        # DB port
        self.user = "root"                      # DB user 
        self.passwd = None                      # DB password
        self.db = None                          # DB 
        self.alias = None                       # DB alias 
        self.pool_max_idle_conns = 10           # 最多允许mysql连接池有多少个空闲连接
        self.pool_max_conns = 20               # mysql连接池上限，0代表无限制
        self.readonly = False 
        
        if kwargs.has_key("slice_range"):
            self.slice_range = kwargs["slice_range"]
        if kwargs.has_key("host"):
            self.host = kwargs["host"]
        if kwargs.has_key("port"):
            self.port = kwargs["port"]
        if kwargs.has_key("user"):
            self.user = kwargs["user"]
        if not kwargs.has_key("passwd"):
            raise DBMetaException("Need DBMeta argument \"passwd\"")
        self.passwd = kwargs["passwd"]
        if not kwargs.has_key("db"):
            raise DBMetaException("Need DBMeta argument \"db\"")
        self.db = kwargs["db"]
        if kwargs.has_key("alias"):
            self.alias = kwargs["alias"]
        if kwargs.has_key("readonly"):
            self.readonly = kwargs["readonly"]
        if kwargs.has_key("pool_max_idle_conns"):
            self.pool_max_idle_conns = kwargs["pool_max_idle_conns"]
        if kwargs.has_key("pool_max_conns"):
            self.pool_max_conns = kwargs["pool_max_conns"]
            
        self._idenity = "%s:%d:%s" % (self.host, self.port, self.db)
    
    def get_identity(self):
        return self._idenity
    
class MySQLInstMgr:
    def __init__(self, *args, **kwargs):
        self._db_conns = {}                             # Key is meta identity, value is dbconn
        self._readonly_db_conns = {}                    # Key is meta identity, value is dbconn
        self._db_conns_robin_status = 0
        self._readonly_db_conns_robin_status = 0
        
        tmp = None
        if len(args) > 0:
            tmp = args[0]
        else:
            tmp = kwargs["metas"]
        self._metas = {}
        for meta in tmp:
            self._metas[meta.get_identity()] = meta 
            self._create_by_meta(meta)
        
    def get_inst_by_hash(self, hval, readonly = False):
        inst = None 
        conns = self._db_conns
        if readonly:
            conns = self._readonly_db_conns 
        
        for (k,v) in conns.items():
            meta = self._metas[k]
            if meta.slice_range and hval >= meta.slice_range[0] and hval <= meta.slice_range[1]:
                inst = v
                break
        return inst
    
    def get_inst_by_random(self, readonly = False, except_inst_ids = None):
        inst = None
        
        conns = self._db_conns 
        if readonly:
            conns = self._readonly_db_conns 
        
        tmp = conns.values()
        tmp2 = []
        if except_inst_ids: 
            for v in tmp:
                if v.meta.get_identity() not in except_inst_ids:
                    tmp2.append(v)
        else:
            tmp2 = tmp 
            
        n = len(tmp2)
        if n == 1:
            inst = tmp2[0]
        elif n > 1:
            inst = tmp2[random.randint(0, n - 1)]
            
        return inst
    
    def get_all_insts(self, readonly = False):
        if readonly:
            return self._readonly_db_conns.values()
        else:
            return self._db_conns.values()
        
    def get_inst(self, readonly = False):
        dbconns = self._db_conns
        if readonly:
            dbconns = self._readonly_db_conns
        if len(dbconns) <= 0:
            return None 
        return dbconns.values()[0]
    
    def get_inst_by_roundrobin(self, readonly = False):
        robin_status = self._db_conns_robin_status
        db_conns = self._db_conns.values()
        if readonly:
            robin_status = self._readonly_db_conns_robin_status
            db_conns = self._readonly_db_conns.values()
        
        if not db_conns:
            return None
        
        i = (len(db_conns) + robin_status + 1) % len(db_conns)
        ret = db_conns[i]
        
        if readonly:
            self._readonly_db_conns_robin_status += 1
        else:
            self._db_conns_robin_status += 1
        return (ret, i)
    
    def get_inst_by_spec_roundrobin(self, rbst, readonly = False):
        db_conns = self._db_conns.values()
        if readonly:
            db_conns = self._readonly_db_conns.values()
        
        n  = len(db_conns)
        i = (n + rbst) % n
        
        return (db_conns[i], i)
    
    def _create_by_meta(self, meta):
        conn = mysql_pool.MysqlPool({"host":meta.host ,
                                         "port":meta.port, 
                                         "user":meta.user, 
                                         "password":meta.passwd, 
                                         "db":meta.db,
                                         "charset":"utf8",
                                         "use_unicode":False,
                                         "connect_timeout":20},
                                         meta.pool_max_idle_conns,
                                         5,
                                        meta.pool_max_conns
                                        )
        conn.meta = meta
        
        logging.info("Init mysql success, dbinfo=%s", meta.get_identity())
        if meta.readonly:
            self._readonly_db_conns[meta.get_identity()] = conn 
        else:
            self._db_conns[meta.get_identity()] = conn




