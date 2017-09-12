import db_helper
import type_define
from base_dao import BaseDAO

from tornado import gen

class JobDAO(BaseDAO):
    def __init__(self, *args, **kwargs):
        BaseDAO.__init__(self, *args, **kwargs)
        self.desc = 'job'
        self.account_tab = 'employee'
        self.record_tab = 'job_record'
        self.node_tab = 'job_node'
        self.attach_tab = 'job_attachment'
        self.file_tab = 'file_path_map'
        self.mark_tab = 'job_status_mark'
        self.auto_path_tab = 'job_auto_path'
        self.auto_path_detail_tab = 'job_auto_path_detail'
        self.broadcast_tab = 'note_broadcast'

    @gen.coroutine
    def clear_all_job_data(self):
        tabs = [self.attach_tab, self.mark_tab, self.node_tab, self.record_tab]
        ret = True
        for tab in tabs:
            sql = "DELETE FROM %s" % tab
            yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def create_new_job(self, **kwargs):
        if 'time' not in kwargs:
            kwargs['time'] = self.now()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.record_tab, **kwargs)
        if ret:
            self.update_job_mark(ret, kwargs['invoker'], type_define.STATUS_JOB_INVOKED_BY_MYSELF)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_base_info(self, job_id):
        sql = "SELECT r.*, i.name AS invoker_name FROM %s r" \
              " LEFT JOIN %s i ON i.id = r.invoker" \
              " WHERE r.status > 0 and r.id=%s" % (self.record_tab, self.account_tab, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def update_job(self, job_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, job_id, self.record_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def delete_job(self, job_id):
        sql = "DELETE FROM %s WHERE id=%s" % (self.record_tab, job_id)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def complete_job(self, job_id, complete_status=type_define.STATUS_JOB_COMPLETED):
        sql = 'UPDATE %s SET status=%s WHERE job_id=%s' % (self.mark_tab, complete_status, job_id)
        yield self._executor.async_update(self._get_inst(), sql)
        yield self.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
        raise gen.Return(True)

    @gen.coroutine
    def add_job_node(self, **kwargs):
        if 'time' not in kwargs:
            kwargs['time'] = self.now()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.node_tab, **kwargs)
        if ret:
            yield self.update_job(kwargs['job_id'], mod_time=kwargs['time'], last_operator=kwargs['sender_id'])
            if 'rec_id' in kwargs and kwargs['rec_id']:
                yield self.update_job_mark(job_id=kwargs['job_id'], uid=kwargs['rec_id'],
                                           status=type_define.STATUS_JOB_MARK_WAITING)
            if 'parent' in kwargs and kwargs['parent']:
                yield self.update_job_mark(job_id=kwargs['job_id'], uid=kwargs['sender_id'],
                                           status=type_define.STATUS_JOB_MARK_PROCESSED)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_node_list(self, job_id):
        sql = "SELECT n.*, a.account, a.name as sender, a.department_id FROM %s n" \
              " LEFT JOIN %s a ON n.sender_id=a.id" \
              " WHERE job_id=%s" % (self.node_tab, self.account_tab, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_node_attachment(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.attach_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_node_attachment_list(self, node_id, attachment_type=type_define.TYPE_JOB_ATTACHMENT_NORMAL):
        sql = "SELECT * FROM %s WHERE node_id=%s AND type=%s" % (self.attach_tab, node_id, attachment_type)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_file_path(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.file_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_file_path(self, path_id):
        sql = 'SELECT * FROM %s WHERE id=%s' % (self.file_tab, path_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def query_job_list(self, job_type=None, invoker=None, count=None, offset=0):
        sql = "SELECT r.*, r.status AS job_status, i.name AS invoker_name, o.name AS last_operator_name FROM %s r" \
              " LEFT JOIN %s i ON i.id = r.invoker" \
              " LEFT JOIN %s o ON o.id = r.last_operator" \
              " WHERE r.status > 0" % (self.record_tab, self.account_tab, self.account_tab)
        if job_type:
            sql += ' AND r.type=%s' % job_type
        if invoker:
            sql += ' AND r.invoker=%s' % invoker
        sql += ' ORDER BY r.id DESC'
        if count:
            sql += ' LIMIT %s, %s' % (offset, count)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_job_mark(self, job_id, uid, status):
        sql = 'SELECT * FROM %s WHERE uid=%s AND job_id=%s' % (self.mark_tab, uid, job_id)
        exist = yield self._executor.async_select(self._get_inst(True), sql)
        if exist:
            ret = yield db_helper.update_table_values(self._get_inst(), self._executor, exist[0]['id'], self.mark_tab,
                                                      status=status)
        else:
            ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.mark_tab,
                                                              job_id=job_id, uid=uid, status=status)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_mark(self, job_id, uid):
        sql = 'SELECT * FROM %s WHERE uid=%s AND job_id=%s' % (self.mark_tab, uid, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def update_job_all_mark(self, job_id, status):
        sql = 'UPDATE %s SET status=%s WHERE job_id=%s' % (self.mark_tab, status, job_id)
        ret = yield self._executor.async_update(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_employee_job(self, uid, status=None, job_type=None, count=None, offset=0):
        sql = 'SELECT m.*, m.status AS mark_status, r.*, r.status AS job_status, i.name AS invoker_name, o.name AS last_operator_name FROM %s m' \
              ' LEFT JOIN %s r ON m.job_id=r.id' \
              " LEFT JOIN %s i ON i.id = r.invoker" \
              " LEFT JOIN %s o ON o.id = r.last_operator" \
              ' WHERE m.uid=%s' \
              % (self.mark_tab, self.record_tab, self.account_tab, self.account_tab, uid,)
        if status is not None:
            sql += ' AND m.status=%s' % status
        if job_type:
            sql += ' AND r.type=%s' % job_type
        sql += ' ORDER BY r.mod_time DESC'
        if count:
            sql += ' LIMIT %s, %s' % (offset, count)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_job_auto_path(self, dept_list, uid_list, **kwargs):
        id = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.auto_path_tab, **kwargs)
        if id:
            if 'pre_path_id' in kwargs:
                yield self.update_job_auto_path(kwargs['pre_path_id'], next_path_id=id)
            if 'next_path_id' in kwargs:
                yield self.update_job_auto_path(kwargs['next_path_id'], pre_path_id=id)
            if 'to_leader' not in kwargs or not kwargs['to_leader']:
                yield self.update_job_auto_path_details(id, dept_list, uid_list)
        raise gen.Return(id)

    @gen.coroutine
    def del_job_auto_path(self, path_id):
        sql = "SELECT * FROM %s WHERE id=%s" % (self.auto_path_tab, path_id)
        path_node = yield self._executor.async_select(self._get_inst(True), sql)
        ret = False
        if path_node:
            path_node = path_node[0]
            yield self.del_job_auto_path_details(path_id)
            if path_node['pre_path_id']:
                yield self.update_job_auto_path(path_node['pre_path_id'], next_path_id=path_node['next_path_id'])
            if path_node['next_path_id']:
                yield self.update_job_auto_path(path_node['next_path_id'], pre_path_id=path_node['pre_path_id'])
            sql = "DELETE FROM %s WHERE id=%s" % (self.auto_path_tab, path_id)
            ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_job_auto_path_details(self, path_id, dept_list, uid_list):
        if uid_list:
            for uid in uid_list:
                yield self.add_job_auto_path_detail(path_id=path_id, uid=uid)
        if dept_list:
            for dept in dept_list:
                yield self.add_job_auto_path_detail(path_id=path_id, dept_id=dept)
        raise gen.Return(True)

    @gen.coroutine
    def del_job_auto_path_details(self, path_id):
        sql = 'DELETE FROM %s WHERE path_id=%s' % (self.auto_path_detail_tab, path_id)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_first_job_auto_path(self, job_type):
        sql = 'SELECT * FROM %s WHERE type=%s AND pre_path_id is NULL' % (self.auto_path_tab, job_type)
        path = yield self._executor.async_select(self._get_inst(True), sql)
        if path:
            path = path[0]
            if not path['to_leader']:
                sql = 'SELECT * FROM %s WHERE path_id=%s' % (self.auto_path_detail_tab, path['id'])
                path['detail'] = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(path)

    @gen.coroutine
    def query_job_auto_path(self, job_type, **kwargs):
        sql = 'SELECT * FROM %s WHERE type=%s' % (self.auto_path_tab, job_type)
        fields = ['id', 'pre_path_id', 'next_path_id']
        exist_field = False
        for field in fields:
            if field in kwargs:
                sql += ' AND %s=%s' % (field, kwargs[field])
                exist_field = True
                break
        path = None
        if exist_field:
            path = yield self._executor.async_select(self._get_inst(True), sql)
            if path:
                path = path[0]
                if not path['to_leader']:
                    sql = 'SELECT * FROM %s WHERE path_id=%s' % (self.auto_path_detail_tab, path['id'])
                    path['detail'] = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(path)

    @gen.coroutine
    def query_job_auto_path_list(self, job_type):
        sql = 'SELECT * FROM %s WHERE type=%s' % (self.auto_path_tab, job_type)
        path_list = yield self._executor.async_select(self._get_inst(True), sql)
        if path_list:
            for path in path_list:
                sql = 'SELECT p.*, d.name as dept, a.name as employee, a.account, a.position, dd.name as uid_dept FROM %s p' \
                      ' LEFT JOIN %s d ON d.id=p.dept_id' \
                      ' LEFT JOIN %s a ON a.id=p.uid' \
                      ' LEFT JOIN %s dd ON dd.id=a.department_id' \
                      ' WHERE p.path_id=%s' \
                      % (self.auto_path_detail_tab, 'department', self.account_tab, 'department', path['id'])
                path['detail'] = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(path_list)

    @gen.coroutine
    def update_job_auto_path(self, path_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, path_id, self.auto_path_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def reset_job_auto_path_detail(self, path_id, uid_list):
        sql = "DELETE FROM %s WHERE path_id=%s" % path_id
        yield self._executor.async_delete(self._get_inst(), sql)
        for uid in uid_list:
            yield self.add_job_auto_path_detail(path_id=id, uid=uid[0], is_dept=[1])
        raise gen.Return(True)

    @gen.coroutine
    def add_job_auto_path_detail(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.auto_path_detail_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def clear_all_job_path_data(self):
        tabs = [self.auto_path_detail_tab, self.auto_path_tab]
        ret = True
        for tab in tabs:
            sql = "DELETE FROM %s" % tab
            yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_memo(self, job_type):
        sql = "SELECT * FROM job_memo WHERE type=%s" % job_type
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def update_job_memo(self, job_type, memo):
        sql = "SELECT * FROM job_memo WHERE type=%s" % job_type
        exist = yield self._executor.async_select(self._get_inst(True), sql)
        if exist:
            sql = "UPDATE job_memo SET memo='%s' WHERE type=%s" % (memo, job_type)
            ret = yield self._executor.async_update(self._get_inst(), sql)
        else:
            ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, 'job_memo', type=job_type, memo=memo)
        raise gen.Return(ret)

    @gen.coroutine
    def cerate_broadcast(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.broadcast_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_broadcast_list(self, **kwargs):
        sql = 'SELECT b.*, a.name, d.name FROM %s b' \
              ' LEFT JOIN employee a ON a.id=b.sender' \
              ' LEFT JOIN department d ON d.id=a.department_id' \
              % (self.broadcast_tab)
        conditions = []
        if 'begin_type' in kwargs:
            if kwargs['begin_type'] == type_define.STATUS_BROADCAST_WOULD_START:
                conditions.append("begin_time>'%s'" % self.now())
            elif kwargs['begin_type'] == type_define.STATUS_BROADCAST_STARTED:
                conditions.append("begin_time<='%s")


