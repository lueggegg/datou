# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_job_handler import JobHandler


class ApiAlterJobPath(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'add')
        job_type = int(self.get_argument_and_check_it('job_type'))
        self.check_job_type(job_type)

        if op == 'add' or op == 'update':
            path_node = {
                'type': job_type,
            }
            path_node['to_leader'] = self.get_argument('to_leader', 0)
            uid_list = None
            dept_list = None
            if not path_node['to_leader']:
                uid_list = self.get_argument('uid_list', None)
                if uid_list is not None:
                    uid_list = self.loads_json(uid_list)
                dept_list = self.get_argument('dept_list', None)
                if dept_list is not None:
                    dept_list = self.loads_json(dept_list)
                if uid_list is None and dept_list is None:
                    self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            if op == 'add':
                fields = ['pre_path_id', 'next_path_id']
                for field in fields:
                    arg = self.get_argument(field, None)
                    if arg:
                        path_node[field] = arg
                msg = '添加处理节点'
                ret = yield self.job_dao.add_job_auto_path(dept_list, uid_list, **path_node)
            else:
                path_id = self.get_argument_and_check_it('path_id')
                yield self.job_dao.del_job_auto_path_details(path_id)
                if path_node['to_leader']:
                    ret = yield self.job_dao.update_job_auto_path(path_id, to_leader=1)
                else:
                    ret = yield self.job_dao.update_job_auto_path_details(path_id, dept_list, uid_list)
                msg = '更新处理节点'
        elif op == 'del':
            path_id = self.get_argument_and_check_it('path_id')
            ret = yield self.job_dao.del_job_auto_path(path_id)
            msg = '删除处理节点'
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

        self.process_result(ret, msg)
