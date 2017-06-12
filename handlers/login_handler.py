# -*- coding: utf-8 -*-

from base_handler import BaseHandler
import error_codes

from tornado import gen

class LoginHandler(BaseHandler):

    @gen.coroutine
    def _deal_request(self):
        BaseHandler._deal_request(self)

        account = self.get_argument('account', None)
        password = self.get_argument('password', None)
        print account, password
        if not account or not password:
            self.redirect_error()
            return

        st, account_info = yield self.check_account(account=account, password=password)
        if st != error_codes.EC_SUCCESS:
            self.write_result(st, '用户不存在')
            return

        self.set_token(account_info['id'], account_info['account'])
        self.write_result(error_codes.EC_SUCCESS)

    def get(self):
        self.render('login.html')

    def post(self):
        return self._deal_request()
