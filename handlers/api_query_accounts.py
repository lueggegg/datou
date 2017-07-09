# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler

import error_codes

class ApiQueryAccountList(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        dept_id = self.get_argument('dept_id', None)
        account_list = yield self.account_dao.query_account_list(dept_id)
        for account in account_list:
            account['portrait'] = self.get_portrait_path(account['portrait'])
        res["data"] = account_list
        self.write_json(res)
