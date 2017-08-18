import db_helper
from base_dao import BaseDAO
import type_define

from tornado import gen

class AccountDAO(BaseDAO):
    def __init__(self, *args, **kwargs):
        BaseDAO.__init__(self, *args, **kwargs)
        self.desc = 'account'
        self.account_tab = 'employee'
        self.dept_tab = 'department'
        self.question_tab = 'protect_question'

    @gen.coroutine
    def add_account(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.account_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_account(self, account, password=None):
        sql = "SELECT a.*, d.name AS dept FROM %s a " \
              "LEFT JOIN %s d ON a.department_id = d.id " \
              "WHERE (a.account='%s' OR a.login_phone='%s') AND a.status!=0" % (self.account_tab, self.dept_tab, account, account)
        if password:
            sql += " AND a.password='%s'" % password
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else False)

    @gen.coroutine
    def query_account_by_id(self, uid):
        sql = "SELECT a.*, d.name AS dept FROM %s a " \
              "LEFT JOIN %s d ON a.department_id = d.id " \
              "WHERE a.id=%s AND a.status=1" % (self.account_tab, self.dept_tab, uid)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else False)

    @gen.coroutine
    def query_account_list(self, dept_id=None, type=type_define.TYPE_ACCOUNT_NORMAL, **kwargs):
        if type == type_define.TYPE_ACCOUNT_CONTACT:
            account_fields = ['id', 'account', 'name', 'department_id', 'cellphone', 'position', 'email', 'qq', 'wechat', 'address']
            account_fields = 'a.' + ', a.'.join(account_fields)
        elif type == type_define.TYPE_ACCOUNT_SAMPLE:
            account_fields = ['id', 'account', 'name', 'department_id', 'position']
            account_fields = 'a.' + ', a.'.join(account_fields)
        else:
            account_fields = 'a.*'
        sql = 'SELECT %s, d.name AS dept, a.id=d.leader AS is_leader FROM %s a ' \
              'LEFT JOIN %s d ON a.department_id = d.id ' \
              'WHERE a.status=1 and d.status=1' % (account_fields, self.account_tab, self.dept_tab)
        if dept_id:
            sql += ' AND a.department_id=%s' % dept_id
        if kwargs:
            conditions = ['account', 'name']
            for condition in conditions:
                if condition in kwargs and kwargs[condition]:
                    sql += " AND a.%s LIKE '%%%s%%'" % (condition, kwargs[condition])
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_account(self, uid, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, uid, self.account_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def add_dept(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.dept_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_dept(self, id=None, name=None):
        sql = "SELECT * FROM %s WHERE status=1" % self.dept_tab
        if id:
            sql += " AND id=%s" % id
        if name:
            sql += " AND name='%s'" % name
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def query_dept_list(self):
        sql = 'SELECT a.*, b.name AS parent_name, c.account AS leader_account, c.name AS leader_name FROM %s a ' \
              'LEFT JOIN %s b ON a.parent=b.id ' \
              'LEFT JOIN %s c ON a.leader=c.id ' \
              'WHERE a.status=1' % (self.dept_tab, self.dept_tab, self.account_tab)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_dept(self, dept_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, dept_id, self.dept_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def delete_dept(self, dept_id):
        sql = 'UPDATE %s SET status=0, login_phone=NULL WHERE department_id=%s' % (self.account_tab, dept_id)
        yield self._executor.async_update(self._get_inst(), sql)
        ret = yield self.update_dept(dept_id, status=0)
        raise gen.Return(ret)

    @gen.coroutine
    def add_protect_question(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.question_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_protect_question(self, question_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, question_id, self.question_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_protect_question(self, uid=None, account=None):
        if uid:
            sql = "SELECT * FROM %s WHERE uid=%s" % (self.question_tab, uid)
        elif account:
            sql = "SELECT q.* FROM %s q INNER JOIN %s a ON q.uid = a.id WHERE a.account='%s'" % (self.question_tab, self.account_tab, account)
        else:
            raise gen.Return(False)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

