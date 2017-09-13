# -*- coding: utf-8 -*-

from api_handler import ApiHandler
from tornado import gen
import error_codes
import type_define

class ApiOperationMask(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument_and_check_it('op')

        ret = False
        msg = ''
        if op == 'add':
            msg = '添加员工权限'
            operation_mask = int(self.get_argument_and_check_it('operation_mask'))
            dept_list = self.get_argument('dept_list', None)
            uid_list = self.get_argument('uid_list', None)
            if dept_list is None and uid_list is None:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            account_list = []
            if dept_list:
                dept_list = self.loads_json(dept_list)
                for dept in dept_list:
                    ret = yield self.account_dao.query_account_list(dept, type_define.TYPE_ACCOUNT_OPERATION_MASK)
                    account_list.extend(ret)
            if uid_list:
                uid_list = self.loads_json(uid_list)
                for uid in uid_list:
                    ret = yield self.account_dao.query_account_by_id(uid)
                    account_list.append(ret)
            for account in account_list:
                ret = yield self.account_dao.update_account(account['id'], operation_mask=account['operation_mask'] | operation_mask)
            ret = True
        elif op == 'change_admin':
            msg = '转移管理员权限'
            uid = self.get_argument_and_check_it('uid')
            ret = yield self.account_dao.update_account(uid, authority=type_define.AUTHORITY_SUPER_ADMIN)
            if ret:
                ret = yield self.account_dao.update_account(self.account_info['id'], authority=1024)
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, 'op错误')

        self.process_result(ret, msg)