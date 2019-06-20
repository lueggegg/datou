# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiHandler
import type_define


class ApiAnnualHandler(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', 'update')
        if op == 'update':
            msg = '更新年假'
            uid = self.get_argument_and_check_it('uid')
            total = self.get_argument_and_check_it('total')
            used = self.get_argument_and_check_it('used')
            ret = yield self.job_dao.query_user_annual_leave(uid)
            if not ret:
                lid = yield self.job_dao.add_annual_leave(uid=uid)
            else:
                lid = ret['id']
            ret = yield self.job_dao.update_user_annual_leave(lid, total=total, used=used)
            self.process_result(ret, msg)
        elif op == 'query':
            uid = self.get_argument_and_check_it('uid')
            ret = yield self.job_dao.query_user_annual_leave(uid)
            if not ret:
                yield self.job_dao.add_annual_leave(uid=uid)
                ret = {
                    'total': 0,
                    'used': 0,
                }
            self.write_data(ret)
