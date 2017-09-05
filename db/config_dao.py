import db_helper
import type_define

from base_dao import BaseDAO
from tornado import gen

class ConfigDAO(BaseDAO):
    def __init__(self, *args, **kwargs):
        BaseDAO.__init__(self, *args, **kwargs)
        self.link_tab = 'outer_link'


    @gen.coroutine
    def add_outer_link(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.link_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_outer_link(self, link_type=type_define.TYPE_NEWS_LINK_COMPANY, count=None, offset=0):
        sql = 'SELECT * FROM %s WHERE type=%s ORDER BY id DESC' % (self.link_tab, link_type)
        if count:
            sql += " LIMIT %s, %s" % (offset, count)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_outer_link(self, link_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, link_id, self.link_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_outer_link(self, link_id):
        sql = 'DELETE FROM %s WHERE id=%s' % (self.link_tab, link_id)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

