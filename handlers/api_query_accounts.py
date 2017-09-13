# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler
import type_define

import error_codes

class ApiQueryAccountList(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        dept_id = self.get_argument('dept_id', None)
        type = self.get_argument('type', None)
        account = self.get_argument('account', None)
        name = self.get_argument('name', None)

        if type:
            type = int(type)

        account_list = yield self.account_dao.query_account_list(dept_id, type, account=account, name=name)
        if len(account_list) > 0 and 'portrait' in account_list[0]:
            for account in account_list:
                account['portrait'] = self.get_portrait_path(account['portrait'])
        if type == type_define.TYPE_ACCOUNT_OPERATION_MASK:
            operation_mask = int(self.get_argument_and_check_it('operation_mask'))
            temp = account_list
            account_list = []
            for account in temp:
                if account['operation_mask'] & operation_mask:
                    account_list.append(account)

        res["data"] = account_list
        self.write_json(res)
