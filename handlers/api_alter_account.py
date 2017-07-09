# -*- coding: utf-8 -*-
import re
import base64
import hashlib
import os

from tornado import gen

import error_codes
from api_handler import ApiHandler


class ApiAlterAccount(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'update')
        if op != 'del':
            data = self.get_argument('account_info', None)
            if not data:
                self.write_result(error_codes.EC_ARGUMENT_ERROR, '参数错误')
                return
            info = self.loads_json(data)

            if 'portrait' in info:
                portrait_data = info['portrait']
                r = re.match('data:image/(.+);base64,(.+)', portrait_data)
                if not r:
                    self.write_result(error_codes.EC_ARGUMENT_ERROR, '证件照文件格式错误')
                    return
                postfix = r.group(1)
                portrait = r.group(2)
                md5 = hashlib.md5()
                md5.update(portrait)
                md5_ret = md5.hexdigest() + '.' + postfix
                file_path = self.get_portrait_path(md5_ret, True)
                if not os.path.isfile(file_path):
                    data = base64.decodestring(portrait)
                    fid = open(file_path, 'wb')
                    fid.write(data)
                    fid.close()
                info['portrait'] = md5_ret

        if op == 'update':
            msg = '更新员工信息'
            uid = self.get_argument('uid', None)
            if not uid:
                self.write_result(error_codes.EC_ARGUMENT_ERROR, '员工id错误')
                return
            ret = self.account_dao.update_account(uid, **info)
        elif op == 'add':
            msg = '添加员工'
            account = yield self.account_dao.query_account(info['account'])
            if account:
                self.write_result(error_codes.EC_SYS_ERROR, '账号已经存在')
                return
            ret = self.account_dao.add_account(**info)
        elif op == 'del':
            msg = '删除员工'
            uid = self.get_argument('uid', None)
            if not uid:
                self.write_result(error_codes.EC_ARGUMENT_ERROR, '员工id错误')
                return
            info = {'status': 0, 'login_phone': None}
            ret = self.account_dao.update_account(uid, **info)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        self.process_result(ret, msg)
