# -*- coding: utf-8 -*-

from tornado import gen
from base_handler import BaseHandler
import error_codes

class ApiHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.send_error(404)

    def process_result(self, ret, msg):
        if not ret:
            self.write_result(error_codes.EC_SYS_ERROR, msg + '失败')
        else:
            self.write_result(error_codes.EC_SUCCESS, msg + '成功')

    @gen.coroutine
    def get_department_map(self):
        dept_list = yield self.account_dao.query_dept_list()
        dept_map = {}
        for item in dept_list:
            dept_map[item['id']] = item
        raise gen.Return(dept_map)

    @gen.coroutine
    def get_department_tree(self):
        dept_list = yield self.account_dao.query_dept_list()
        dept_tree = {}
        for dept in dept_list:
            if dept['id'] not in dept_tree:
                dept_tree[dept['id']] = [dept]
            else:
                dept_tree[dept['id']].insert(0, dept)
            if dept['parent']:
                if dept['parent'] not in dept_tree:
                    dept_tree[dept['parent']] = [dept]
                else:
                    dept_tree[dept['parent']].append(dept)
        raise gen.Return(dept_tree)

class ApiNoVerifyHandler(ApiHandler):
    def post(self, *args, **kwargs):
        return self._deal_request(False)