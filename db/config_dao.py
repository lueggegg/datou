import db_helper
import type_define

from base_dao import BaseDAO
from tornado import gen

class ConfigDAO(BaseDAO):
    def __init__(self, *args, **kwargs):
        BaseDAO.__init__(self, *args, **kwargs)
        self.link_tab = 'outer_link'
        self.download_type_tab = 'download_type'
        self.download_detail_tab = 'download_detail'
        self.rule_type_tab = 'rule_type'
        self.rule_detail_tab = 'rule_detail'
        self.config_tab = 'common_config'


    @gen.coroutine
    def add_outer_link(self, **kwargs):
        if 'mod_time' not in kwargs:
            kwargs['mod_time'] = self.now()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.link_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_outer_link(self, link_type=type_define.TYPE_NEWS_LINK_COMPANY, count=None, offset=0):
        sql = 'SELECT * FROM %s WHERE type=%s ORDER BY mod_time DESC' % (self.link_tab, link_type)
        if count:
            sql += " LIMIT %s, %s" % (offset, count)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_outer_link(self, link_id, **kwargs):
        if 'mod_time' not in kwargs:
            kwargs['mod_time'] = self.now()
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, link_id, self.link_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_outer_link(self, link_id):
        sql = 'DELETE FROM %s WHERE id=%s' % (self.link_tab, link_id)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_rule_type(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.rule_type_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_rule_type(self, type_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, type_id, self.rule_type_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_rule_type(self, type_id):
        ret = yield self.update_rule_type(type_id, status=0)
        raise gen.Return(ret)

    @gen.coroutine
    def query_rule_type_list(self):
        sql = 'SELECT * FROM %s WHERE status=1' % (self.rule_type_tab)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_rule_detail(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.rule_detail_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_rule_detail(self, detail_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, detail_id, self.rule_detail_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_rule_detail(self, detail_id):
        ret = yield db_helper.delete_table_by_id(self._get_inst(), self._executor, self.rule_detail_tab, detail_id)
        raise gen.Return(ret)

    @gen.coroutine
    def query_rule_detail_list(self, type_id=None):
        sql = "SELECT * FROM %s" % self.rule_detail_tab
        if type_id:
            sql += " WHERE type_id=%s" % type_id
        sql += ' ORDER BY title'
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_download_type(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.download_type_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_download_type(self, type_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, type_id, self.download_type_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_download_type(self, type_id):
        ret = yield self.update_download_type(type_id, status=0)
        raise gen.Return(ret)

    @gen.coroutine
    def query_download_type_list(self, parent_type=None):
        sql = 'SELECT * FROM %s WHERE status=1' % (self.download_type_tab)
        if parent_type:
            sql += ' AND type=%s' % parent_type
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_download_detail(self, **kwargs):
        if 'upload_date' not in kwargs:
            kwargs['upload_date'] = self.today()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.download_detail_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_download_detail(self, detail_id):
        ret = yield db_helper.delete_table_by_id(self._get_inst(), self._executor, self.download_detail_tab, detail_id)
        raise gen.Return(ret)

    @gen.coroutine
    def query_download_detail_list(self, type_id=None):
        sql = "SELECT * FROM %s" % self.download_detail_tab
        if type_id:
            sql += " WHERE type_id=%s" % type_id
        sql += ' ORDER BY upload_date DESC'
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def set_common_config(self, config_type, key, label):
        sql = 'SELECT * FROM %s WHERE type=%s AND key_id=%s' % (self.config_tab, config_type, key)
        exist = yield self._executor.async_select(self._get_inst(True), sql)
        if exist:
            yield db_helper.update_table_values(self._get_inst(), self._executor, exist[0]['id'], self.config_tab, label=label)
        else:
            yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.config_tab, type=config_type, key_id=key, label=label)
        raise gen.Return(True)

    @gen.coroutine
    def query_common_config(self, config_type):
        sql = 'SELECT * FROM %s WHERE type=%s ORDER BY key_id' % (self.config_tab, config_type)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)
