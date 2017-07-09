import mysql_executor
import db_helper

from tornado import gen

class AccountDAOException(Exception):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message


class AccountDAO:
    def __init__(self, *args, **kwargs):
        self.account_tab = 'employee'
        self.dept_tab = 'department'
        self.question_tab = 'protect_question'

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
            raise AccountDAOException("Get account mysql instance error, not found")
        return inst


    @gen.coroutine
    def add_account(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.account_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_account(self, account, password=None):
        sql = "SELECT a.*, d.name AS dept FROM %s a " \
              "LEFT JOIN %s d ON a.department_id = d.id " \
              "WHERE (a.account='%s' OR a.login_phone='%s') AND a.status=1" % (self.account_tab, self.dept_tab, account, account)
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
    def query_account_list(self, dept_id=None):
        sql = 'SELECT * FROM %s WHERE status=1' % (self.account_tab)
        if dept_id:
            sql += ' AND department_id=%s' % dept_id
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
    def query_dept_list(self):
        sql = 'SELECT a.*, b.name AS parent_name FROM %s a LEFT JOIN %s b ON a.parent=b.id WHERE a.status=1' % (self.dept_tab, self.dept_tab)
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

