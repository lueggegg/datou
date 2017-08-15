# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_job_handler import JobHandler

import error_codes

class ApiQueryJobStatusMark(JobHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        job_id = self.get_argument_and_check_it('job_id')
        uid = self.get_argument('uid', self.account_info['id'])

        ret = yield self.job_dao.query_job_mark(job_id, uid)

        res['data'] = ret

        self.write_json(res)
