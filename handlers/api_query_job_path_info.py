# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_job_handler import JobHandler

import error_codes
import type_define

class ApiQueryJobPathInfo(JobHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        job_type = int(self.get_argument_and_check_it('type'))
        self.check_job_type(job_type)

        ret = yield self.job_dao.query_job_auto_path_list(job_type)
        res['data'] = ret

        self.write_json(res)
