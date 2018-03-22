# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler

import error_codes

class ApiQueryLeaveList(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        query_date = self.get_argument('date', None)
        ret = yield self.job_dao.query_leave_list(query_date)
        res["data"] = ret
        self.write_json(res)
