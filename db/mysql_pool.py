# -*- coding: utf-8 -*-
import tornado_mysql.pools
from tornado.gen import coroutine, Return


class MysqlPool(tornado_mysql.pools.Pool):
    def __init__(self,
                 connect_kwargs,
                 max_idle_connections=1,
                 max_recycle_sec=3600,
                 max_open_connections=0,
                 io_loop=None, ):
        tornado_mysql.pools.Pool.__init__(self,
                                          connect_kwargs,
                                          max_idle_connections,
                                          max_recycle_sec,
                                          max_open_connections,
                                          io_loop)

    @coroutine
    def execute_whit_insert_id(self, query, params=None, cursor=None):
        conn = yield self._get_conn()
        try:
            cur = conn.cursor(cursor)
            yield cur.execute(query, params)
            insert_id = conn.insert_id()
            yield cur.close()
        except:
            self._close_conn(conn)
            raise
        else:
            self._put_conn(conn)
        raise Return((cur, insert_id))
