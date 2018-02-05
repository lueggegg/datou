import db_helper
import type_define
import datetime
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
        self.uid_set_tab = 'uid_set'
        self.uid_set_detail_tab = 'uid_set_detail'
        self.notify_tab = 'job_notify'
        self.uid_path_detail_table = 'job_uid_path_detail'
        self.admin_job_tab = 'admin_job'
        self.timer_task_tab = 'job_timer_task'
        self.leave_detail_tab = 'leave_detail'

    @gen.coroutine
    def clear_all_job_data(self):
        tabs = [self.notify_tab, self.uid_path_detail_table, self.attach_tab, self.mark_tab, self.node_tab, self.record_tab]
        ret = True
        for tab in tabs:
            sql = "DELETE FROM %s" % tab
            yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def create_new_job(self, with_mark=True, **kwargs):
        if 'time' not in kwargs:
            kwargs['time'] = self.now()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.record_tab, **kwargs)
        if ret and with_mark:
            self.update_job_mark(ret, kwargs['invoker'], type_define.STATUS_JOB_INVOKED_BY_MYSELF)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_base_info(self, job_id):
        sql = "SELECT r.*, r.status AS job_status, i.name AS invoker_name FROM %s r" \
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
        yield db_helper.update_table_values(self._get_inst(), self._executor, job_id, self.record_tab, status=complete_status)
        if complete_status == type_define.STATUS_JOB_CANCEL:
            yield self.delete_job_mark(job_id)
        else:
            yield self.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)

        raise gen.Return(True)

    @gen.coroutine
    def add_job_node(self, is_comment=False, **kwargs):
        if 'time' not in kwargs:
            kwargs['time'] = self.now()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.node_tab, **kwargs)
        if ret and not is_comment:
            yield self.update_job(kwargs['job_id'], mod_time=kwargs['time'], last_operator=kwargs['sender_id'])
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_node_list(self, job_id, branch_id=None, count=None):
        sql = "SELECT n.*, a.account, a.name as sender, a.department_id, d.name AS dept FROM %s n" \
              " LEFT JOIN %s a ON n.sender_id=a.id" \
              " LEFT JOIN department d ON a.department_id=d.id" \
              " WHERE job_id=%s" % (self.node_tab, self.account_tab, job_id)
        if branch_id:
            sql += " AND branch_id=%s" % branch_id
        else:
            sql += " AND branch_id is NULL"
        if count:
            sql += ' LIMIT %s' % count
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_first_job_node(self, job_id):
        sql = 'SELECT * FROM %s WHERE job_id=%s ORDER BY id LIMIT 1' % (self.node_tab, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

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
    def query_job_list(self, job_type=None, invoker=None, count=None, offset=0, **kwargs):
        sql = "SELECT r.*, r.id AS job_id, r.status AS job_status, i.name AS invoker_name, o.name AS last_operator_name FROM %s r" \
              " LEFT JOIN %s i ON i.id = r.invoker" \
              " LEFT JOIN %s o ON o.id = r.last_operator" \
              " WHERE r.status > 0" % (self.record_tab, self.account_tab, self.account_tab)
        if job_type:
            sql += ' AND r.type=%s' % job_type
        elif 'type_list' in kwargs:
            type_list = kwargs['type_list']
            if len(type_list) == 1:
                sql += ' AND r.type=%s' % type_list[0]
            else:
                sql += ' AND r.type IN %s' % (tuple(type_list), )
        elif 'exclude_type' in kwargs:
            exclude_type = kwargs['exclude_type']
            if len(exclude_type) == 1:
                sql += ' AND r.type != %s' % exclude_type[0]
            else:
                sql += ' AND r.type NOT IN %s' % (tuple(exclude_type),)
        if invoker:
            sql += ' AND r.invoker=%s' % invoker
        if 'status_list' in kwargs:
            status_list = kwargs['status_list']
            if len(status_list) == 1:
                sql += ' AND r.status=%s' % status_list[0]
            else:
                sql += ' AND r.status IN %s' % (tuple(status_list),)
        if 'begin_time' in kwargs:
            sql += " AND r.time >= '%s'" % kwargs['begin_time']
        if 'end_time' in kwargs:
            sql += " AND r.time < '%s'" % (datetime.datetime.strptime(kwargs['end_time'], '%Y-%m-%d') + datetime.timedelta(days=1))
        if 'invoker_set' in kwargs:
            invoker_set = kwargs['invoker_set']
            if len(invoker_set) == 1:
                sql += ' AND invoker=%s' % invoker_set[0]
            else:
                sql += ' AND invoker IN %s' % (tuple(invoker_set),)
        if 'title' in kwargs:
            sql += " AND r.title LIKE '%%%s%%'" % kwargs['title']
        if 'last_operator' in kwargs and kwargs['last_operator']:
            sql += ' AND r.last_operator=%s' % kwargs['last_operator']
        sql += ' ORDER BY r.mod_time DESC'
        total_count = None
        if 'total_count' not in kwargs or not kwargs['total_count']:
            total_count_sql = self.get_count_sql(sql)
            total_count = yield self._executor.async_select(self._get_inst(True), total_count_sql)
            total_count = total_count[0]['records_count']
        if count:
            sql += ' LIMIT %s, %s' % (offset, count)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return((ret, total_count))

    @gen.coroutine
    def update_job_mark(self, job_id, uid, status, branch_id=None):
        sql = 'SELECT * FROM %s WHERE uid=%s AND job_id=%s' % (self.mark_tab, uid, job_id)
        if branch_id:
            sql += ' AND branch_id=%s' % branch_id
        exist = yield self._executor.async_select(self._get_inst(True), sql)
        if exist:
            ret = yield db_helper.update_table_values(self._get_inst(), self._executor, exist[0]['id'], self.mark_tab,
                                                      status=status)
        else:
            info = {'job_id': job_id, 'uid': uid, 'status': status}
            if branch_id:
                info['branch_id'] = branch_id
            ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.mark_tab, **info)
        raise gen.Return(ret)

    @gen.coroutine
    def set_all_group_job_read(self, uid):
        sql = 'SELECT m.id FROM %s m ' \
              ' LEFT JOIN %s r ON r.id = m.job_id' \
              ' WHERE m.status=%s AND r.sub_type=%s AND m.uid=%s'\
              % (self.mark_tab, self.record_tab,
                 type_define.STATUS_JOB_MARK_WAITING, type_define.TYPE_JOB_SUB_TYPE_GROUP, uid)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        if ret:
            if len(ret) > 1:
                id_list = [item['id'] for item in ret]
                sql = 'UPDATE %s SET status=%d' \
                    ' WHERE id IN %s' % (self.mark_tab, type_define.STATUS_JOB_MARK_PROCESSED, tuple(id_list))
            else:
                sql = 'UPDATE %s SET status=%d' \
                    ' WHERE id=%s' % (self.mark_tab, type_define.STATUS_JOB_MARK_PROCESSED, ret[0]['id'])
            ret = yield self._executor.async_update(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_mark(self, job_id, uid, branch_id=None):
        sql = 'SELECT * FROM %s WHERE uid=%s AND job_id=%s' % (self.mark_tab, uid, job_id)
        if branch_id:
            sql += ' AND branch_id=%s' % branch_id
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def update_job_all_mark(self, job_id, status, filter_list=None):
        sql = 'UPDATE %s SET status=%s WHERE job_id=%s' % (self.mark_tab, status, job_id)
        if isinstance(filter_list, int):
            sql += ' AND uid != %s' % filter_list
        elif isinstance(filter_list, list):
            if len(filter_list) == 1:
                sql += ' AND uid != %s' % filter_list[0]
            else:
                sql += ' AND uid IN %s' % (tuple(filter_list),)
        ret = yield self._executor.async_update(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def delete_job_mark(self, job_id, filter_list=None):
        sql = 'DELETE FROM %s WHERE job_id=%s' % (self.mark_tab, job_id)
        if isinstance(filter_list, int):
            sql += ' AND uid != %s' % filter_list
        elif isinstance(filter_list, list):
            if len(filter_list) == 1:
                sql += ' AND uid != %s' % filter_list[0]
            else:
                sql += ' AND uid IN %s' % (tuple(filter_list),)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_employee_job(self, uid, status=None, job_type=None, count=None, offset=0, **kwargs):
        sql = 'SELECT m.*, m.status AS mark_status, r.*, r.status AS job_status, i.name AS invoker_name, o.name AS last_operator_name FROM %s m' \
              ' LEFT JOIN %s r ON m.job_id=r.id' \
              " LEFT JOIN %s i ON i.id = r.invoker" \
              " LEFT JOIN %s o ON o.id = r.last_operator" \
              ' WHERE m.uid=%s and r.status > 0' \
              % (self.mark_tab, self.record_tab, self.account_tab, self.account_tab, uid,)
        if status is not None:
            sql += ' AND m.status=%s' % status
        else:
            sql += ' AND m.status!=%s' % type_define.STATUS_JOB_MARK_SYS_MSG
        if job_type:
            sql += ' AND r.type=%s' % job_type
        if 'title' in kwargs:
            sql += " AND r.title LIKE '%%%s%%'" % kwargs['title']
        if 'begin_time' in kwargs:
            sql += " AND r.time >= '%s'" % kwargs['begin_time']
        if 'end_time' in kwargs:
            sql += " AND r.time < '%s'" % (datetime.datetime.strptime(kwargs['end_time'], '%Y-%m-%d') + datetime.timedelta(days=1))
        sql += ' ORDER BY r.mod_time DESC'
        total_count = None
        if 'total_count' not in kwargs or not kwargs['total_count']:
            total_count_sql = self.get_count_sql(sql)
            total_count = yield self._executor.async_select(self._get_inst(True), total_count_sql)
            total_count = total_count[0]['records_count']
        if count:
            sql += ' LIMIT %s, %s' % (int(offset), int(count))
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return((ret, total_count))

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

    @gen.coroutine
    def create_uid_set(self):
        set_id = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.uid_set_tab)
        raise gen.Return(set_id)

    @gen.coroutine
    def create_uid_set_detail(self, set_id, uid_set):
        for uid in uid_set:
            ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor,
                                                              self.uid_set_detail_tab, uid=uid, set_id=set_id)
            if not ret:
                raise gen.Return(False)
        raise gen.Return(True)

    @gen.coroutine
    def insert_into_uid_set(self, set_id, uid_set):
        size = len(uid_set)
        if size == 0:
            raise gen.Return(True)
        if size == 1:
            uid = uid_set.pop()
            sql = 'SELECT uid FROM %s WHERE set_id=%s AND uid=%s' % (self.uid_set_detail_tab, set_id, uid)
            ret = yield self._executor.async_select(self._get_inst(True), sql)
            if not ret:
                ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor,
                                                                  self.uid_set_detail_tab, uid=uid, set_id=set_id)
        else:
            uids = tuple(uid_set)
            sql = 'SELECT uid FROM %s WHERE set_id=%s AND uid in %s' % (self.uid_set_detail_tab, set_id, uids)
            ret = yield self._executor.async_select(self._get_inst(True), sql)
            for item in ret:
                uid_set.remove(item['uid'])
            ret = yield self.create_uid_set_detail(set_id, uid_set)
        raise gen.Return(ret)


    @gen.coroutine
    def query_uid_set(self, set_id, sample=False):
        if sample:
            sql = 'SELECT * FROM %s WHERE set_id=%s' % (self.uid_set_detail_tab, set_id)
        else:
            sql = 'SELECT s.uid, a.account, a.name, d.name AS dept FROM %s s' \
                  ' LEFT JOIN %s a ON s.uid=a.id' \
                  ' LEFT JOIN department d ON a.department_id=d.id' \
                  ' WHERE s.set_id=%s' % (self.uid_set_detail_tab, self.account_tab, set_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def job_notify(self, job_id, uid_list, notify_type):
        for uid in uid_list:
            yield self.add_notify_item(job_id, uid, notify_type)
        raise gen.Return(True)

    @gen.coroutine
    def add_notify_item(self, job_id, uid, notify_type):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.notify_tab,
                            job_id=job_id, uid=uid, type=notify_type)
        raise gen.Return(ret)

    @gen.coroutine
    def del_notify_item(self, job_id, uid):
        sql = 'DELETE FROM %s WHERE job_id=%s AND uid=%s' % (self.notify_tab, job_id, uid)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_notify_job_list(self, uid, notify_type, **kwargs):
        sql = "SELECT r.*, r.status AS job_status, i.name AS invoker_name FROM %s r" \
              " LEFT JOIN %s i ON i.id=r.invoker" \
              " LEFT JOIN %s n ON n.job_id=r.id" \
              " WHERE r.status > 0 AND n.uid=%s AND n.type=%s ORDER BY r.mod_time DESC" \
              % (self.record_tab, self.account_tab, self.notify_tab, uid, notify_type)
        if 'count' in kwargs and kwargs['count']:
            offset = kwargs['offset'] if 'offset' in kwargs and kwargs['offset'] else 0
            sql += ' LIMIT %s, %s' % (offset, kwargs['count'])
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_job_uid_path_detail(self, job_id, index, uid=None, set_id=None):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.uid_path_detail_table,
                                                          job_id=job_id, uid=uid, set_id=set_id, order_index=index)
        raise gen.Return(ret)

    @gen.coroutine
    def del_job_uid_path_detail(self, job_id, index):
        sql = 'DELETE FROM %s WHERE job_id=%s AND order_index=%s' % (self.uid_path_detail_table, job_id, index)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_uid_path_detail(self, job_id):
        sql = 'SELECT * FROM %s WHERE job_id=%s' % (self.uid_path_detail_table, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def get_job_uid_path_detail(self, job_id, index):
        sql = 'SELECT * FROM %s WHERE job_id=%s and order_index=%s' % (self.uid_path_detail_table, job_id, index)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def create_admin_job(self, **kwargs):
        kwargs['mod_time'] = self.now()
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.admin_job_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_admin_job(self, job_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, job_id, self.admin_job_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def query_admin_job(self, job_id):
        sql = 'SELECT * FROM %s WHERE id=%s' % (self.admin_job_tab, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def query_admin_job_list(self, count=None, offset=0, **kwargs):
        sql = 'SELECT j.*, a.name, a.account, a.cellphone, a.id_card FROM %s j' \
              ' LEFT JOIN %s a ON j.invoker=a.id' % (self.admin_job_tab, self.account_tab)
        if kwargs:
            condition = []
            for key in kwargs:
                condition.append('j.%s=%s' % (key, kwargs[key]))
            sql += ' WHERE %s' % ' AND '.join(condition)
        sql += ' ORDER BY j.id DESC'
        total_count = None
        if count:
            total_count_sql = self.get_count_sql(sql)
            total_count = yield self._executor.async_select(self._get_inst(True), total_count_sql)
            total_count = total_count[0]['records_count']
            sql += ' LIMIT %s, %s' % (offset, count)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return((ret, total_count))

    @gen.coroutine
    def add_job_timer_task(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.timer_task_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_job_timer_task(self, task_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, task_id, self.timer_task_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def del_job_timer_task(self, job_id):
        sql = 'DELETE FROM %s WHERE job_id=%s' % (self.timer_task_tab, job_id)
        ret = yield self._executor.async_delete(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_job_timer_task(self, job_id):
        sql = 'SELECT * FROM %s WHERE job_id=%s' % (self.timer_task_tab, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def query_job_timer_task_list(self):
        sql = 'SELECT * FROM %s' % self.timer_task_tab
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def add_leave_detail(self, **kwargs):
        ret = yield db_helper.insert_into_table_return_id(self._get_inst(), self._executor, self.leave_detail_tab, **kwargs)
        raise gen.Return(ret)

    @gen.coroutine
    def update_leave_detail(self, job_id, half_day):
        sql = "UPDATE %s SET half_day=%s WHERE job_id=%s" % (self.leave_detail_tab, half_day, job_id)
        ret = yield self._executor.async_update(self._get_inst(), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_leave_detail(self, job_id):
        sql = "SELECT * FROM %s WHERE job_id=%s" % (self.leave_detail_tab, job_id)
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret[0] if ret else None)

    @gen.coroutine
    def query_leave_detail_list(self, **kwargs):
        sql = 'SELECT t.*, j.type, j.invoker, a.name, d.name AS dept FROM %s t' \
              ' LEFT JOIN %s j ON j.id=t.job_id' \
              ' LEFT JOIN %s a ON a.id=j.invoker' \
              ' LEFT JOIN %s d ON d.id=a.department_id WHERE j.status=%s' \
              '' % (self.leave_detail_tab, self.record_tab, self.account_tab, 'department', type_define.STATUS_JOB_COMPLETED)
        order = ' ORDER BY a.department_id, a.id, t.begin_time'
        if 'min_begin_time' in kwargs:
            sql += " AND t.begin_time>='%s'" % kwargs['min_begin_time']
        if 'max_begin_time' in kwargs:
            sql += " AND t.begin_time<='%s'" % kwargs['max_begin_time']
        if 'dept_id' in kwargs:
            sql += " AND d.id=%s" % kwargs['dept_id']
        if 'type_list' in kwargs:
            type_list = kwargs['type_list']
            if len(type_list) == 1:
                sql += ' AND j.type=%s' % type_list[0]
            else:
                sql += ' AND j.type IN %s' % (tuple(type_list),)
        if 'leave_type' in kwargs:
            sql += " AND t.leave_type='%s'" % kwargs['leave_type']
        sql += order
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def query_html_tag_job_node_list(self):
        sql = "SELECT id, content FROM %s WHERE content LIKE '%%<%%>%%'" % self.node_tab
        ret = yield self._executor.async_select(self._get_inst(True), sql)
        raise gen.Return(ret)

    @gen.coroutine
    def update_job_node(self, node_id, **kwargs):
        ret = yield db_helper.update_table_values(self._get_inst(), self._executor, node_id, self.node_tab, **kwargs)
        raise gen.Return(ret)


