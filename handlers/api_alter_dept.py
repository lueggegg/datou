# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiHandler
import type_define


class ApiAlterDept(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'update')
        if op != 'del':
            data = self.get_argument('dept_info', None)
            if not data:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            info = self.loads_json(data)

        if op == 'update':
            msg = '更新部门'
            dept_id = self.get_argument('dept_id', None)
            if not dept_id:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '部门id错误')
            if 'leader' in info:
                dept_map = yield self.get_department_map()
                dept = dept_map[int(dept_id)]
                if dept['leader'] == int(info['leader']):
                    self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '设置失败，部门主管未变化')
                if dept['leader']:
                    ori_leader = yield self.account_dao.query_account_by_id(dept['leader'])
                else:
                    ori_leader = None
                if ori_leader and ori_leader['authority'] == type_define.AUTHORITY_DEPT_LEADER:
                    yield self.account_dao.update_account(ori_leader['id'], authority=1024)
                new_leader = yield self.account_dao.query_account_by_id(info['leader'])
                if new_leader['authority'] > type_define.AUTHORITY_DEPT_LEADER:
                    yield self.account_dao.update_account(new_leader['id'], authority=type_define.AUTHORITY_DEPT_LEADER)
                if self.get_argument('relative_report', None):
                    yield self.account_dao.update_dept_report_uid(dept_id, info['leader'])
                if dept['parent']:
                    parent_dept = dept_map[dept['parent']]
                    if parent_dept['leader']:
                        yield self.account_dao.update_account(info['leader'], report_uid=parent_dept['leader'])
            if 'parent' in info and info['parent']:
                dept_map = yield self.get_department_map()
                dept = dept_map[int(dept_id)]
                parent = dept_map[int(info['parent'])]
                if dept['leader'] and parent['leader']:
                    yield self.account_dao.update_account(dept['leader'], report_uid=parent['leader'])
            ret = self.account_dao.update_dept(dept_id, **info)
        elif op == 'add':
            msg = '添加部门'
            ret = self.account_dao.add_dept(**info)
        elif op == 'del':
            msg = '删除部门'
            dept_id = self.get_argument('dept_id', None)
            if not dept_id:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '部门id错误')
            dept_id = int(dept_id)
            dept_tree = yield self.get_department_tree()
            ret = yield self.travel_del_dept(dept_tree, dept_id)
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

        self.on_dept_info_changed()
        self.process_result(ret, msg)


    @gen.coroutine
    def travel_del_dept(self, dept_tree, dept_id):
        if len(dept_tree[dept_id]) == 1:
            rs = yield self.account_dao.delete_dept(dept_id)
            raise gen.Return(rs)
        for dept in dept_tree[dept_id][1:]:
            yield self.travel_del_dept(dept_tree, dept['id'])
        rs = yield self.account_dao.delete_dept(dept_id)
        raise gen.Return(rs)
