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
    def get_via_and_chair_leader(self, uid):
        current_account = yield self.account_dao.query_account_by_id(uid)
        if current_account['authority'] in [type_define.AUTHORITY_CHAIR_LEADER, type_define.AUTHORITY_VIA_LEADER]:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '领导不适用此接口')

        ret = {'via': None, 'chair': None}
        count = 5
        while True:
            if not current_account['report_uid']:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置汇报关系')
            current_account = yield self.account_dao.query_account_by_id(current_account['report_uid'])
            if current_account['authority'] == type_define.AUTHORITY_VIA_LEADER:
                ret['via'] = current_account
                continue
            if current_account['authority'] == type_define.AUTHORITY_CHAIR_LEADER:
                ret['chair'] = current_account
                break
            count -= 1
            if count == 0:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '遍历汇报关系出错：层次过多')
        raise gen.Return(ret)

