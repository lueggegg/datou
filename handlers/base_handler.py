# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import hashlib
import json
import os
from datetime import datetime

from tornado import gen

import error_codes
import utils

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(obj, datetime.timedelta):
            return "%02d:%02d:%02d" % (obj.seconds / 3600, obj.seconds % 3600 / 60, obj.seconds % 60)

        return json.JSONEncoder.default(self, obj)


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        RequestHandler.__init__(self, application, request, **kwargs)
        self.account_dao = self.settings['account_dao']
        self.account_info = None
        self.psd_question = None
        self.cookie_expires_days = 10

    def post(self, *args, **kwargs):
        return self._deal_request()

    def get(self, *args, **kwargs):
        return self._deal_request()

    @gen.coroutine
    def _deal_request(self, verify=True):
        if verify:
            st = yield self.verify_user()
            if not st:
                return
        try:
            yield self._real_deal_request()
        except Exception, e:
            self.write_result(error_codes.EC_UNKNOW_ERROR, '程序异常')
            return

    @gen.coroutine
    def _real_deal_request(self):
        pass

    @gen.coroutine
    def check_account(self, **kwargs):
        if 'uid' in kwargs:
            self.account_info = yield self.account_dao.query_account_by_id(kwargs['uid'])
        elif 'password' in kwargs and 'account' in kwargs:
            self.account_info = yield self.account_dao.query_account(kwargs['account'], kwargs['password'])

        if not self.account_info:
            raise gen.Return((error_codes.EC_USER_NOT_EXIST, None))

        self.account_info['portrait'] = self.get_portrait_path(self.account_info['portrait'])
        raise gen.Return((error_codes.EC_SUCCESS, self.account_info))

    def redirect_error(self):
        self.redirect('error.html')

    def redirect_login(self):
        self.redirect('login.html')

    @gen.coroutine
    def write_result(self, result, msg=''):
        self.write_json({'status': result, 'msg': msg})

    def set_token(self, uid, account):
        self.set_secure_cookie('uid', str(uid), self.cookie_expires_days)
        self.set_secure_cookie('account', account, self.cookie_expires_days)

    def get_token(self):
        uid = self.get_secure_cookie('uid')
        account = self.get_secure_cookie('account')
        return (uid, account)

    @gen.coroutine
    def clear_token(self):
        self.clear_cookie('uid')
        self.clear_cookie('account')

    @gen.coroutine
    def verify_user(self):
        if self.settings['test_mode']:
            self.account_info = {'id': 5, 'account': 'test', 'name': 'test_name',
                'portrait': '4f705390ffbbf1c46691ddfa0b839d8b.png',
                'authority': 1,
            }
            raise gen.Return(True)

        uid, account = self.get_token()
        if not uid or not account:
            self.redirect_login()
            raise gen.Return(False)
        st, account_info = yield self.check_account(uid=uid)
        if st != error_codes.EC_SUCCESS:
            self.redirect_login()
            raise gen.Return(False)
        if account_info['account'] != account:
            self.redirect_login()
            raise gen.Return(False)
        self.account_info = account_info
        raise gen.Return(True)

    @gen.coroutine
    def write_json(self, res):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(res, encoding='utf8', cls=MyEncoder, ensure_ascii=False))

    def loads_json(self, arg):
        return json.loads(arg, object_hook=utils.decode_dict)

    def get_portrait_path(self, filename, local=False):
        path = '/res/images/portrait/' + filename
        if local:
            path = self.get_template_path() + path
        return path

    def get_hash(self, string):
        md5 = hashlib.md5()
        md5.update(string)
        sha1 = hashlib.sha1()
        sha1.update(md5.hexdigest())
        return sha1.hexdigest()
