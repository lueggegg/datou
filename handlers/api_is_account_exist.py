# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiNoVerifyHandler


class ApiIsAccountExist(ApiNoVerifyHandler):
    @gen.coroutine
    def _real_deal_request(self):
        account = self.get_argument('account', None)
        if not account:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '账号参数错误')
            return
        res = {"status": error_codes.EC_SUCCESS}
        ret = yield self.account_dao.query_account(account)
        if not ret:
            self.write_result(error_codes.EC_UNKNOWN_ERROR, '账号不存在')
        else:
            res['data'] = ret['id']
            self.write_json(res)
