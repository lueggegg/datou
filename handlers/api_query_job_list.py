# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler
from auto_job_util import UtilAutoJob

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
        if job_type is not None:
            job_type = int(job_type)

        total = None
        if query_type == type_define.TYPE_JOB_QUERY_AUTO_JOB:
            query_content = self.get_argument('query_content', None)
            if query_content:
                kwargs = self.loads_json(query_content)
            else:
                kwargs = {}
            kwargs['status_list'] = [type_define.STATUS_JOB_COMPLETED, type_define.STATUS_JOB_REJECTED]
            if job_type is None:
                kwargs['type_list'] = UtilAutoJob.get_auto_job_type_list()
            elif job_type == type_define.TYPE_JOB_HR_ASK_FOR_LEAVE:
                kwargs['type_list'] = [
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY,
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY,
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY,
                    type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY,
                ]
                job_type = None
            elif job_type == type_define.TYPE_JOB_HR_LEAVE_FOR_BORN:
                kwargs['type_list'] = [
                    type_define.TYPE_JOB_LEAVE_FOR_BORN_LEADER,
                    type_define.TYPE_JOB_LEAVE_FOR_BORN_NORMAL,
                ]
                job_type = None
            ret, total = yield self.job_dao.query_job_list(job_type=job_type, count=count, offset=offset, **kwargs)
        elif query_type == type_define.TYPE_JOB_QUERY_DOC_REPORT:
            query_content = self.get_argument('query_content', None)
            if query_content:
                kwargs = self.loads_json(query_content)
            else:
                kwargs = {}
            job_status = int(self.get_argument('job_status', 1))
            if job_status == 1:
                kwargs['status_list'] = [type_define.STATUS_JOB_COMPLETED]
            elif job_status == 2:
                kwargs['status_list'] = [type_define.STATUS_JOB_PROCESSING]
            else:
                kwargs['status_list'] = [type_define.STATUS_JOB_COMPLETED, type_define.STATUS_JOB_PROCESSING]
            if not job_type:
                kwargs['type_list'] = [type_define.TYPE_JOB_OFFICIAL_DOC, type_define.TYPE_JOB_DOC_REPORT]
            ret, total = yield self.job_dao.query_job_list(job_type=job_type, count=count, offset=offset, **kwargs)
        elif query_type == type_define.TYPE_JOB_QUERY_SYS_MSG:
            ret, total = yield self.job_dao.query_job_list(job_type=type_define.TYPE_JOB_SYSTEM_MSG, count=count, offset=offset)
        elif query_type == type_define.TYPE_JOB_QUERY_DYNAMIC:
            ret, total = yield self.job_dao.query_job_list(job_type=type_define.TYPE_JOB_DYNAMIC, last_operator=uid, count=count, offset=offset)
        elif query_type == type_define.TYPE_JOB_QUERY_NOTIFY_AUTO_JOB:
            ret = yield self.job_dao.query_notify_job_list(self.account_info['id'], type_define.TYPE_JOB_NOTIFY_AUTO_JOB, count=count, offset=offset)
        elif query_type == type_define.TYPE_JOB_QUERY_NOTIFY_DOC_REPORT:
            ret = yield self.job_dao.query_notify_job_list(self.account_info['id'], type_define.TYPE_JOB_NOTIFY_DOC_REPORT, count=count, offset=offset)
        elif query_type == type_define.TYPE_JOB_QUERY_NOTIFY_SYS_MSG:
            ret = yield self.job_dao.query_notify_job_list(self.account_info['id'], type_define.TYPE_JOB_NOTIFY_SYS_MSG, count=count, offset=offset)
        else:
            query_content = self.get_argument('query_content', None)
            if query_content:
                kwargs = self.loads_json(query_content)
            else:
                kwargs = {}
            if status == type_define.STATUS_JOB_INVOKED_BY_MYSELF:
                ret, total = yield self.job_dao.query_job_list(job_type, uid, count, offset, **kwargs)
            else:
                ret, total = yield self.job_dao.query_employee_job(uid, status, job_type, count, offset, **kwargs)

        res['data'] = ret
        res['total'] = total
        self.write_json(res)
