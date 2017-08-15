# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define
from api_handler import ApiHandler


class ApiAlterJob(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'complete')
        job_id = self.get_argument('job_id', None)
        if op == 'complete' or op == 'cancel':
            if not job_id:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数job_id错误')
            if op == 'cancel':
                complete_status = type_define.STATUS_JOB_CANCEL
                msg = '撤回工作流'
            else:
                complete_status = type_define.STATUS_JOB_COMPLETED
                msg = '归档工作流'
            ret = yield self.job_dao.complete_job(job_id, complete_status)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        self.on_dept_info_changed()
        self.process_result(ret, msg)
