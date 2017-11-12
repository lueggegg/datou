# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
import hashlib
import json
import os
import datetime
import config
import logging
import traceback

from tornado import gen

import error_codes
import utils

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return ' '

        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")

        if isinstance(obj, datetime.timedelta):
            return "%02d:%02d:%02d" % (obj.seconds / 3600, obj.seconds % 3600 / 60, obj.seconds % 60)

        return json.JSONEncoder.default(self, obj)

    @staticmethod
    def dumps_json(obj):
        return json.dumps(obj, encoding='utf8', cls=MyEncoder, ensure_ascii=False)

    @staticmethod
    def loads_json(arg):
        return json.loads(arg, object_hook=utils.decode_dict)


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        RequestHandler.__init__(self, application, request, **kwargs)
        self.account_dao = self.settings['account_dao']
        self.job_dao = self.settings['job_dao']
        self.config_dao = self.settings['config_dao']
        self.job_timer = self.settings['job_timer']
        self.account_info = None
        self.psd_question = None
        self.cookie_expires_days = 10
        self.end_notification = Exception('finish notification')
        self.push_server = self.settings['push_server']

    def get_tag(self):
        return 'base'

    def post(self, *args, **kwargs):
        return self._deal_request()

    def get(self, *args, **kwargs):
        return self._deal_request()

    @gen.coroutine
    def _deal_request(self, verify=True):
        self.debug_info(self.request.arguments)
        if verify and not self.get_argument('all_allow', None):
            st = yield self.verify_user()
            if not st:
                return
        try:
            yield self._real_deal_request()
        except Exception, e:
            if e is not self.end_notification:
                self.elog('exception %s' % self.dump_exp(e))
                self.write_result(error_codes.EC_UNKNOWN_ERROR, '程序异常')
            return

    @gen.coroutine
    def _real_deal_request(self):
        pass

    @gen.coroutine
    def check_account(self, **kwargs):
        if 'uid' in kwargs:
            self.account_info = yield self.account_dao.query_account_by_id(kwargs['uid'])
        elif 'password' in kwargs and 'account' in kwargs:
            self.account_info = yield self.account_dao.query_account(kwargs['account'])
            if self.account_info and self.account_info['password'] != kwargs['password']:
                raise gen.Return((error_codes.EC_PASSWORD_ERROR, '密码错误'))


        if not self.account_info:
            self.wlog(self.dumps_json(kwargs))
            raise gen.Return((error_codes.EC_USER_NOT_EXIST, '账号不存在或已经失效'))

        self.account_info['portrait'] = self.get_portrait_path(self.account_info['portrait'])
        if self.get_tag() != 'api':
            self.account_dao.update_account(self.account_info['id'], last_op_time=self.now())
        self.debug_info(self.get_main_account_info())
        raise gen.Return((error_codes.EC_SUCCESS, self.account_info))

    def get_main_account_info(self, account=None):
        if account is None:
            account = self.account_info
        fields = ['id', 'account', 'name', 'dept']
        result = {}
        for f in fields:
            if f in account:
                result[f] = account[f]
        return result

    def generate_extend(self, account_info):
        if 'extend' in account_info:
            if account_info['extend']:
                account_info['extend'] = self.loads_json(account_info['extend'])
            else:
                extend_field = ['name', 'sex', 'birthday', 'politics', 'id_card', 'position',
                            'education_level', 'college', 'degree', 'major',
                            'join_date', 'cellphone', 'address',]
                extend = {}
                for field in extend_field:
                    extend[field] = account_info[field]
                account_info['extend'] = extend

    def redirect_error(self):
        self.redirect('error.html')

    def redirect_login(self):
        self.redirect('login.html')

    def redirect_index(self):
        self.redirect('/index.html')

    def write_result(self, result, msg=''):
        self.write_json({'status': result, 'msg': msg})

    def finish_with_error(self, err_code, msg):
        self.elog('%s: %s' % (err_code, msg))
        self.write_result(err_code, msg)
        raise self.end_notification

    def get_argument_and_check_it(self, arg_name, error_msg=None):
        arg = self.get_argument(arg_name, None)
        if not error_msg:
            error_msg = '缺少参数%s' % arg_name
        if arg is None:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, error_msg)
        return arg

    def check_result_and_finish_while_failed(self, ret, error_msg='系统错误'):
        if not ret:
            self.finish_with_error(error_codes.EC_SYS_ERROR, error_msg)


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
    def write_data(self, data):
        self.write_json({'status': error_codes.EC_SUCCESS, 'data': data})

    @gen.coroutine
    def write_json(self, res):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(self.dumps_json(res))

    def loads_json(self, arg):
        return MyEncoder.loads_json(arg)

    def dumps_json(self, obj):
        return MyEncoder.dumps_json(obj)

    def get_portrait_path(self, filename, local=False):
        return self.get_res_file_path(filename, 'res/images/portrait', local)

    def get_res_file_path(self, filename, res_dir, local=False):
        path = os.path.join(res_dir, filename)
        if local:
            path = os.path.join(self.get_template_path(), path)
        return path.replace('\\', '/')

    def get_hash(self, string):
        md5 = hashlib.md5()
        md5.update(string)
        sha1 = hashlib.sha1()
        sha1.update(md5.hexdigest())
        return sha1.hexdigest()

    def get_current_hash(self):
        return self.get_hash('%s' % self.now())

    def is_valid_datetime(self, time, format='%Y-%m-%d'):
        try:
            datetime.datetime.strptime(time, format)
            return True
        except Exception, e:
            return False

    def now(self):
        return datetime.datetime.now()

    def today(self):
        return datetime.date.today()

    def __get_logging_msg(self, msg):
        return '{%s: %s }' % (self.__class__, msg)

    def dump_exp(self, e):
        return "exp=\"%s\" trace=\"%s\"" % (str(e), traceback.format_exc())

    def elog(self, msg):
        logging.error(self.__get_logging_msg(msg))

    def wlog(self, msg):
        logging.warning(self.__get_logging_msg(msg))

    def ilog(self, msg):
        logging.info(self.__get_logging_msg(msg))

    def dlog(self, msg):
        logging.debug(self.__get_logging_msg(msg))

    def debug_info(self, info):
        if config.enable_debug_log:
            info = self.dumps_json(info)
            if len(info) < 2078:
                self.dlog()

