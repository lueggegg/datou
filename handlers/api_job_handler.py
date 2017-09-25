# -*- coding: utf-8 -*-

import type_define
import error_codes
from tornado import gen

from api_handler import ApiHandler

class JobHandler(ApiHandler):

    def check_job_type(self, job_type):
        valid = job_type > type_define.TYPE_JOB_BEGIN and job_type < type_define.TYPE_JOB_END
        if not valid:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '工作流类型错误')

    @gen.coroutine
    def get_account_leader(self, uid, level, need_list=False):
        if level not in ['dept', 'via', 'chair']:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '系统错误')

        current_account = yield self.account_dao.query_account_by_id(uid)
        if current_account['authority'] in [type_define.AUTHORITY_CHAIR_LEADER, type_define.AUTHORITY_VIA_LEADER]:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '领导不适用此接口')

        need_authority = None
        if level == 'dept':
            need_authority = type_define.AUTHORITY_DEPT_LEADER
        elif level == 'via':
            need_authority = type_define.AUTHORITY_VIA_LEADER
        elif level == 'chair':
            need_authority = type_define.AUTHORITY_CHAIR_LEADER
        count = 5
        leader_list = []
        while True:
            authority = current_account['authority']
            if authority > type_define.AUTHORITY_ADMIN and authority <= type_define.AUTHORITY_DEPT_LEADER:
                leader_list.append(current_account['id'])
            if authority > type_define.AUTHORITY_ADMIN and authority <= need_authority:
                break
            if not current_account['report_uid']:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置汇报关系')
            current_account = yield self.account_dao.query_account_by_id(current_account['report_uid'])
            count -= 1
            if count == 0:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '遍历汇报关系出错：层次过多')
        raise gen.Return(leader_list if need_list else current_account)

