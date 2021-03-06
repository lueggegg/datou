# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiHandler


class ApiQueryAccountExtend(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        uid = self.get_argument('uid', self.account_info['id'])

        account_info = yield self.account_dao.query_account_by_id(uid, True)
        if not account_info:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '该用户不存在')
        account_info['portrait'] = self.get_portrait_path(account_info['portrait'])

        self.generate_extend(account_info)
        res = {
            "status": error_codes.EC_SUCCESS,
            "data": {
                'extend': account_info['extend'],
                'portrait': account_info['portrait'],
                'dept': account_info['dept'],
                'department_id': account_info['department_id'],
                'operation_mask': account_info['operation_mask'],
                'report_name': account_info['report_name'],
                'report_uid': account_info['report_uid'],
                'authority': account_info['authority']
            }
        }

        self.write_json(res)
