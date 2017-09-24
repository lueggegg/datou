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
        ret = True
        if op == 'cancel':
            msg = '撤回工作流'
            ret = yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_CANCEL)
        elif op == 'complete':
            msg = '归档工作流'
            ret = yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_COMPLETED)
            notify = self.get_argument('notify', None)
            if notify:
                yield self.job_dao.notify_doc_report_mark(job_id, type_define.OPERATION_MASK_QUERY_REPORT)
        elif op == 'read':
            msg = '更新工作流状态'
            status = self.get_argument('status', type_define.STATUS_JOB_MARK_COMPLETED)
            yield self.job_dao.update_job_mark(job_id, self.account_info['id'], status)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        self.process_result(ret, msg)
