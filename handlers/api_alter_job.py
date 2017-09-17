# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define
from api_handler import ApiHandler


class ApiAlterJob(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'complete')
        job_id = self.get_argument_and_check_it('job_id', None)
        if op == 'cancel':
            msg = '撤回工作流'
            ret = yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_CANCEL)
        elif op == 'complete':
            msg = '归档工作流'
            ret = yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_COMPLETED)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        self.process_result(ret, msg)
