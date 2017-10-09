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
        self.account_prefix = 'S'

    @gen.coroutine
    def add_account(self, **kwargs):
        if 'account' not in kwargs:
            sql = 'SELECT MAX(id) AS max_id FROM %s' % self.account_tab
            max_id = yield self._executor.async_select(self._get_inst(True), sql)
            if max_id:
                kwargs['account'] = '%s%s' % (self.account_prefix, 10000 + max_id[0]['max_id'])
            else:
                kwargs['account'] = '%s%s' % (self.account_prefix, 10001)
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.account_tab, **kwargs)
        raise gen.Return({'id': ret, 'account': kwargs['account']} if ret else None)

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
    def query_pure_account(self, account):
        sql = "SELECT * FROM %s WHERE account='%s' OR login_phone='%s'" % (self.account_tab, account, account)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else False)



    @gen.coroutine
    def query_account_by_id(self, uid, with_report_uid=False):
        if with_report_uid:
            sql = "SELECT a.*, aa.name AS report_name, d.name AS dept FROM %s a " \
                  "LEFT JOIN %s d ON a.department_id = d.id " \
                  "LEFT JOIN %s aa ON a.report_uid = aa.id " \
                  "WHERE a.id=%s AND a.status=1" % (self.account_tab, self.dept_tab, self.account_tab, uid)
        else:
            sql = "SELECT a.*, d.name AS dept FROM %s a " \
                  "LEFT JOIN %s d ON a.department_id = d.id " \
                  "WHERE a.id=%s AND a.status=1" % (self.account_tab, self.dept_tab, uid)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else False)

    @gen.coroutine
    def query_account_list(self, dept_id=None, field_type=type_define.TYPE_ACCOUNT_NORMAL, **kwargs):
        if field_type == type_define.TYPE_ACCOUNT_JUST_ID:
            sql = 'SELECT a.id FROM %s a WHERE a.status=1' % (self.account_tab,)
        else:
            if field_type == type_define.TYPE_ACCOUNT_CONTACT:
                account_fields = ['id', 'account', 'name', 'department_id', 'cellphone', 'position', 'email', 'qq', 'wechat', 'address', 'weight']
                account_fields = 'a.' + ', a.'.join(account_fields)
            elif field_type == type_define.TYPE_ACCOUNT_SAMPLE or field_type == type_define.TYPE_ACCOUNT_LEADER:
                account_fields = ['id', 'account', 'name', 'department_id', 'position', 'weight']
                account_fields = 'a.' + ', a.'.join(account_fields)
            elif field_type == type_define.TYPE_ACCOUNT_BIRTHDAY:
                account_fields = ['id', 'account', 'name', 'department_id', 'birthday', 'join_date', 'sex', 'position_type', 'weight']
                account_fields = 'a.' + ', a.'.join(account_fields)
            elif field_type == type_define.TYPE_ACCOUNT_OPERATION_MASK:
                account_fields = ['id', 'account', 'name', 'operation_mask']
                account_fields = 'a.' + ', a.'.join(account_fields)
            else:
                account_fields = 'a.*'
            sql = 'SELECT %s, d.name AS dept, a.id=d.leader AS is_leader FROM %s a ' \
                  'LEFT JOIN %s d ON a.department_id = d.id ' \
                  'WHERE a.status=1 and d.status=1' % (account_fields, self.account_tab, self.dept_tab)
        if dept_id:
            sql += ' AND a.department_id=%s' % dept_id
        if field_type == type_define.TYPE_ACCOUNT_LEADER:
            sql += ' AND (a.operation_mask & %s OR a.operation_mask & %s)' % (type_define.AUTHORITY_CHAIR_LEADER, type_define.AUTHORITY_VIA_LEADER)
        if kwargs:
            conditions = ['account', 'name']
            for condition in conditions:
                if condition in kwargs and kwargs[condition]:
                    sql += " AND a.%s LIKE '%%%s%%'" % (condition, kwargs[condition])
            if 'operation_mask' in kwargs and kwargs['operation_mask']:
                sql += ' AND a.operation_mask & %s' % kwargs['operation_mask']
            if 'uid_list' in kwargs:
                uid_list = kwargs['uid_list']
                if len(uid_list) == 1:
                    sql += ' AND a.id=%s' % uid_list[0]
                else:
                    sql += ' AND a.id IN %s' % (tuple(uid_list),)
        sql += ' ORDER BY a.weight DESC'
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_account(self, uid, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, uid, self.account_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_dept_report_uid(self, dept_id, leader_id):
        sql = 'UPDATE %s SET report_uid=%s WHERE department_id=%s and id!=%s and status' % (self.account_tab, leader_id, dept_id, leader_id)
        ret = yield self._executor.async_update(self._get_inst(), sql)
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
              'WHERE a.status=1 ORDER BY weight DESC' % (self.dept_tab, self.dept_tab, self.account_tab)
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

