# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiHandler
import type_define

class ApiQueryAccountList(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        dept_id = self.get_argument('dept_id', None)
        filed_type = self.get_argument('type', None)
        account = self.get_argument('account', None)
        name = self.get_argument('name', None)
        operation_mask = self.get_argument('operation_mask', None)
        # status = self.get_argument('status', None)
        status = int(self.get_argument('status', type_define.STATUS_EMPLOYEE_NORMAL))
        if status == -1:
            status = None

        if filed_type:
            filed_type = int(filed_type)

        account_list = yield self.account_dao.query_account_list(dept_id, filed_type, account=account, name=name,
                    operation_mask=operation_mask, status=status)
        if len(account_list) > 0 and 'portrait' in account_list[0]:
            for account in account_list:
                account['portrait'] = self.get_portrait_path(account['portrait'])

        res["data"] = account_list
        self.write_json(res)
