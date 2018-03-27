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
        push_content = None
        if op == 'cancel':
            msg = '撤回工作流'
            ret = yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_CANCEL)
        elif op == 'complete':
            msg = '归档工作流'
            ret = yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_COMPLETED)
            notify_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_JUST_ID, operation_mask=type_define.OPERATION_MASK_QUERY_REPORT)
            notify_list = [item['id'] for item in notify_list]
            yield self.job_dao.job_notify(job_id, notify_list, type_define.TYPE_JOB_NOTIFY_DOC_REPORT)
            push_content = "【已归档】"
        elif op == 'notify_read':
            msg = '工作流通知已读'
            yield self.job_dao.del_notify_item(job_id, self.account_info['id'])
        elif op == 'group_doc_read':
            msg = '群组公文已读'
            job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
            if job_mark and job_mark['status'] == type_define.STATUS_JOB_MARK_WAITING:
                yield self.job_dao.update_job_mark(job_id, self.account_info['id'], type_define.STATUS_JOB_MARK_PROCESSED)
        elif op == 'group_all_read':
            msg = '设置所有未读为已读'
            yield self.job_dao.set_all_group_job_read(self.account_info['id'])
        elif op == 'delete':
            msg = '删除工作流'
            if not self.is_developer():
                self.finish_with_error(error_codes.EC_HAS_NO_AUTHORITY, '仅开发权限可以删除')
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_INVALID)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        while push_content:
            job_record = yield self.job_dao.query_job_base_info(job_id)
            ret = yield self.job_dao.query_job_relative_uid_list(job_id)
            if not ret:
                break
            push_alias = ret
            if self.account_info['id'] in push_alias:
                push_alias.remove(self.account_info['id'])
            extra = {
                "type": job_record['type'],
                "job_id": job_id,
                'title': job_record['title'],
                'content': push_content,
                'sender': self.account_info['name']
            }
            self.push_server.push_with_alias("", push_alias, extra)
            break

        self.process_result(ret, msg)
