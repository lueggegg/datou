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
                notify_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_JUST_ID, operation_mask=type_define.OPERATION_MASK_QUERY_REPORT)
                notify_list = [item['id'] for item in notify_list]
                yield self.job_dao.job_notify(job_id, notify_list, type_define.TYPE_JOB_NOTIFY_DOC_REPORT)
        elif op == 'notify_read':
            msg = '工作流通知已读'
            yield self.job_dao.del_notify_item(job_id, self.account_info['id'])
        elif op == 'group_doc_read':
            msg = '群组公文已读'
            job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
            if job_mark and job_mark['status'] == type_define.STATUS_JOB_MARK_WAITING:
                yield self.job_dao.update_job_mark(job_id, self.account_info['id'], type_define.STATUS_JOB_MARK_PROCESSED)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        self.process_result(ret, msg)
