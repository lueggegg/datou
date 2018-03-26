import mysql_executor
import datetime
import re
from tornado import gen

class DAOException(Exception):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message


class BaseDAO:
    def __init__(self, *args, **kwargs):
        self.desc = 'base'
        if len(args) > 0:
            self._inst_mgr = args[0]
        else:
            self._inst_mgr = kwargs["inst_mgr"]

        self._executor = mysql_executor.MySQLExecutor()

    def _get_inst(self, readonly=False):
        inst = None

        if readonly:
            inst = self._inst_mgr.get_inst_by_random(readonly)

        # Second try get rw instance
        if not inst:
            inst = self._inst_mgr.get_inst_by_random()

        if not inst:
            raise DAOException("Get %s mysql instance error, not found" % self.desc)
        return inst

    @gen.coroutine
    def execute_sql(self, sql, read_only=False):
        ret = yield self._executor.async_select(self._get_inst(read_only), sql)
        raise gen.Return(ret)

    def get_count_sql(self, sql, alias='records_count'):
        p = re.compile(r'select .+ from')
        return p.sub(r'select count(*) as %s from' % alias, sql.lower())

    def now(self):
        return datetime.datetime.now()

    def today(self):
        return datetime.date.today()