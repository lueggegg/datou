# -*- coding: utf-8 -*-
import re
import base64
import hashlib
import os

from tornado import gen

import error_codes
import type_define
from api_handler import ApiHandler


class ApiAlterAccount(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'update')
        if op != 'status':
            data = self.get_argument('account_info', None)
            if not data:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            info = self.loads_json(data)

            if 'portrait' in info:
                portrait_data = info['portrait']
                r = re.match('data:image/(.+);base64,(.+)', portrait_data)
                if not r:
                    self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '证件照文件格式错误')
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


        extend_field = ['name', 'birthday', 'politics', 'id_card', 'position',
                        'education_level', 'college', 'degree', 'major',
                        'join_date', 'cellphone', 'address',]
        if op == 'update':
            msg = '更新员工信息'
            uid = self.get_argument('uid', None)
            if not uid:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '员工id错误')
            account = yield self.account_dao.query_account_by_id(uid)
            if not account:
                self.finish_with_error(error_codes.EC_USER_NOT_EXIST, '员工不存在')

            if 'login_phone' in info:
                exist = yield self.account_dao.query_pure_account(info['login_phone'])
                if exist:
                    self.finish_with_error(error_codes.EC_SYS_ERROR, '该手机号码已经被绑定')
            self.get_info_from_extend(info, extend_field)
            if 'id_card' in info and info['id_card'] and not account['birthday'] and 'birthday' not in info:
                info['birthday'] = self.get_birthday_from_id_card(info['id_card'])
                self.check_birthday(info['birthday'])
            if 'report_uid' not in info and 'department_id' in info:
                self.set_default_report_uid(info, info['department_id'])
            ret = self.account_dao.update_account(uid, **info)
        elif op == 'add':
            msg = '添加员工'
            self.get_info_from_extend(info, extend_field)
            yield self.init_report_uid(info)
            if 'password' not in info:
                info['password'] = self.get_hash('oa123456')
            if 'birthday' not in info:
                info['birthday'] = self.get_birthday_from_id_card(info['id_card'])
            self.check_birthday(info['birthday'])
            if 'portrait' not in info:
                info['portrait'] = 'default_portrait.png'
            if 'report_uid' not in info:
                self.set_default_report_uid(info, info['department_id'])
            ret = yield self.account_dao.add_account(**info)
            if ret:
                self.write_json({
                    'status': error_codes.EC_SUCCESS,
                    'data': ret,
                })
                return
        elif op == 'status':
            msg = '修改员工状态'
            uid = self.get_argument('uid', None)
            if not uid:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '员工id错误')
            status = self.get_argument('status', type_define.STATUS_EMPLOYEE_INVALID)
            info = {'status': status}
            if status != type_define.STATUS_EMPLOYEE_NORMAL:
                info['login_phone'] = None
            ret = self.account_dao.update_account(uid, **info)
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

        self.process_result(ret, msg)

    @gen.coroutine
    def set_default_report_uid(self, account_info, dept_id):
        dept_map = yield self.get_department_map()
        dept_id = int(dept_id)
        account_info['report_uid'] = dept_map[dept_id]['leader']


    def get_info_from_extend(self, info, extend_field):
            if 'extend' in info:
                extend = info['extend']
                for field in extend_field:
                    if field in extend:
                        info[field] = extend[field]
                if 'birthday' in extend and not extend['birthday']:
                    info['birthday'] = self.get_birthday_from_id_card(info['id_card'])
                    self.check_birthday(info['birthday'])
                info['extend'] = self.dumps_json(extend)

    def check_birthday(self, birthday):
        if not self.is_valid_datetime(birthday):
            self.finish_with_error(error_codes.EC_SYS_ERROR, '无效的日期')

    def get_birthday_from_id_card(self, id_card):
        return '%s-%s-%s' % (id_card[6:10], id_card[10:12], id_card[12:14])

    @gen.coroutine
    def init_report_uid(self, account):
        if account['report_uid']:
            return
        dept_map = yield self.get_department_map()
        dept = dept_map[int(account['department_id'])]
        account['report_uid'] = dept['leader']