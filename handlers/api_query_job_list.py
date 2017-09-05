# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler

import error_codes
import type_define

class ApiQueryJobList(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        uid = self.get_argument('uid', self.account_info['id'])
        job_type = self.get_argument('job_type', None)
        count = self.get_argument('count', None)
        offset = self.get_argument('offset', 0)
        status = self.get_argument('status', None)
        if status is not None:
            status = int(status)

        if status == type_define.STATUS_JOB_INVOKED_BY_MYSELF:
            ret = yield self.job_dao.query_job_list(job_type, uid, count, offset)
        else:
            ret = yield self.job_dao.query_employee_job(uid, status, job_type, count, offset)

        res['data'] = ret
        self.write_json(res)
