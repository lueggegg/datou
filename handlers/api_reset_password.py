# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiNoVerifyHandler


class ApiResetPassword(ApiNoVerifyHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        password = self.get_argument('uid', None)
        uid = self.get_argument('uid', None)
        ret = self.account_dao.update_account(uid, password=password)

        self.process_result(ret, '重置密码')

