# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiNoVerifyHandler


class ApiResetPassword(ApiNoVerifyHandler):

    @gen.coroutine
    def _real_deal_request(self):
        password = self.get_argument('password', None)
        uid = self.get_argument('uid', None)
        ret = self.account_dao.update_account(uid, password=password)

        self.process_result(ret, '重置密码')

