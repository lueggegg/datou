# -*- coding: utf-8 -*-

from base_handler import BaseHandler
import error_codes
from tornado import gen
import codecs
import os
import json

class ApiUpdateLoginPhone(BaseHandler):

    @gen.coroutine
    def _deal_request(self):
        st = yield self.verify_user()
        if not st:
            return
        try:
            phone = self.get_argument('login_phone', None)
            if phone is None:
                self.write_result(error_codes.EC_ARGUMENT_ERROR, '参数错误')
                return
            if phone == self.account_info['login_phone']:
                self.write_result(error_codes.EC_SUCCESS)
                return
            for account in self.accounts.values():
                if account['id'] == self.account_info['id']:
                    continue
                if account['login_phone'] == phone:
                    self.write_result(error_codes.EC_LOGIN_PHONE_BIND, '该手机号码已经被其他用户绑定')
                    return

            self.account_info['login_phone'] = phone
            fid = codecs.open(os.path.join(os.path.dirname(__file__), "account.txt"), 'w', 'utf8')
            fid.write(json.dumps(self.accounts, ensure_ascii=False, encoding='utf8'))
            fid.close()
            self.write_result(error_codes.EC_SUCCESS)

        except Exception, e:
            self.write_result(error_codes.EC_SYS_ERROR, '系统错误')

    def post(self, *args, **kwargs):
        self._deal_request()

    @gen.coroutine
    def get(self, *args, **kwargs):
        self.send_error(404)
