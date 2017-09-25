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
        query_type = int(self.get_argument('query_type', 0))
        if status is not None:
            status = int(status)

        if query_type == type_define.TYPE_JOB_QUERY_AUTO_JOB:
            query_content = self.get_argument('query_content', None)
            if query_content:
                kwargs = self.loads_json(query_content)
            else:
                kwargs = {}
            kwargs['status_list'] = [type_define.STATUS_JOB_COMPLETED, type_define.STATUS_JOB_REJECTED]
            kwargs['exclude_type'] = [type_define.TYPE_JOB_OFFICIAL_DOC, type_define.TYPE_JOB_DOC_REPORT]
            if job_type == type_define.TYPE_JOB_HR_ASK_FOR_LEAVE:
                kwargs['type_list'] = [
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY,
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY,
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY,
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY,
                ]
            elif job_type == type_define.TYPE_JOB_HR_LEAVE_FOR_BORN:
                kwargs['type_list'] = [
                    type_define.TYPE_JOB_LEAVE_FOR_BORN_LEADER,
                    type_define.TYPE_JOB_LEAVE_FOR_BORN_NORMAL,
                ]
            ret = yield self.job_dao.query_job_list(job_type=job_type, count=count, offset=offset, **kwargs)
        elif query_type == type_define.TYPE_JOB_QUERY_DOC_REPORT:
            query_content = self.get_argument('query_content', None)
            if query_content:
                kwargs = self.loads_json(query_content)
            else:
                kwargs = {}
            kwargs['status_list'] = [type_define.STATUS_JOB_COMPLETED, type_define.STATUS_JOB_REJECTED]
            job_type = type_define.TYPE_JOB_DOC_REPORT
            ret = yield self.job_dao.query_job_list(job_type=job_type, count=count, offset=offset, **kwargs)
        elif query_type == type_define.TYPE_JOB_QUERY_NOTIFY_AUTO_JOB:
            ret = yield self.job_dao.query_notify_job_list(self.account_info['id'], type_define.TYPE_JOB_NOTIFY_AUTO_JOB)
        elif query_type == type_define.TYPE_JOB_QUERY_NOTIFY_DOC_REPORT:
            ret = yield self.job_dao.query_notify_job_list(self.account_info['id'], type_define.TYPE_JOB_NOTIFY_DOC_REPORT)
        else:
            if status == type_define.STATUS_JOB_INVOKED_BY_MYSELF:
                ret = yield self.job_dao.query_job_list(job_type, uid, count, offset)
            else:
                ret = yield self.job_dao.query_employee_job(uid, status, job_type, count, offset)

        res['data'] = ret
        self.write_json(res)
