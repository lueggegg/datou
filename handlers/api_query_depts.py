# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler

import error_codes

class ApiQueryDeptList(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        tree = self.get_argument('tree', None)
        if tree is None:
            dept_list = yield self.account_dao.query_dept_list()
        else:
            dept_list = yield self.get_department_tree(with_level=True)
        res["data"] = dept_list
        self.write_json(res)
