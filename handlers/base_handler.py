# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import hashlib
import json
import os
from datetime import datetime

from tornado import gen

import error_codes
import utils

def get_hash(string):
    md5 = hashlib.md5()
    md5.update(string)
    sha1 = hashlib.sha1()
    sha1.update(md5.hexdigest())
    return sha1.hexdigest()


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
        self.account_info = None
        self.psd_question = None
        self.cookie_expires_days = 100
        fid = open(os.path.join(os.path.dirname(__file__), "account.txt"), 'r')
        data = fid.read()
        fid.close()
        self.accounts = json.loads(data, 'utf8')
        fid = open(os.path.join(os.path.dirname(__file__), "psd_question.txt"), 'r')
        data = fid.read()
        fid.close()
        if len(data) > 0:
            self.psd_questions = json.loads(data, 'utf8')
        else:
            self.psd_questions = {}

    @gen.coroutine
    def _deal_request(self):
        # self.set_header("Content-Type", "application/json; charset=utf-8")
        pass

    @gen.coroutine
    def check_account(self, **kwargs):
        if 'uid' in kwargs:
            if kwargs['uid'] in self.accounts:
                self.account_info = self.accounts[kwargs['uid']]
        elif 'password' in kwargs and 'account' in kwargs:
            for account in self.accounts.values():
                if account['account'] == kwargs['account'] and account['password'] == kwargs['password']:
                    self.account_info = account
                elif account['login_phone'] == kwargs['account'] and account['password'] == kwargs['password']:
                    self.account_info = account

        if not self.account_info:
            raise gen.Return((error_codes.EC_USER_NOT_EXIST, None))

        if str(self.account_info['id']) in self.psd_questions:
            self.psd_question = self.psd_questions[str(self.account_info['id'])]

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
