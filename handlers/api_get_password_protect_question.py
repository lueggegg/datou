# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiNoVerifyHandler


class ApiGetPasswordProtectQuestion(ApiNoVerifyHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        uid = self.get_argument('uid', None)
        account = self.get_argument('account', None)
        if uid:
            question_list = yield self.account_dao.query_protect_question(uid=uid)
        elif account:
            question_list = yield self.account_dao.query_protect_question(account=account)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            return
        # for item in question_list:
        #     item['answer'] = self.get_hash(item['answer'])
        res["data"] = question_list if question_list else None
        self.write_json(res)

