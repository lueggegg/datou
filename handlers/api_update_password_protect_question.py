# -*- coding: utf-8 -*-

from api_handler import ApiHandler
import error_codes
from tornado import gen
import codecs
import os
import json

class ApiUpdatePasswordPretectQuestion(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        data = self.get_argument('question_info', None)
        if not data:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            return
        question_info = self.loads_json(data)

        op = self.get_argument('op', None)
        if op == 'add':
            msg = '添加密保问题'
            ret = False
            for pair in question_info:
                ret = yield self.account_dao.add_protect_question(uid=self.account_info['id'], question=pair[0], answer=pair[1])
                if not ret:
                    break
        elif op == 'update':
            msg = '更新密保问题'
            question_id = self.get_argument('question_id', None)
            if not question_id:
                self.write_result(error_codes.EC_ARGUMENT_ERROR, '密保问题id错误')
                return
            ret = yield self.account_dao.update_protect_question(question_id, **question_info)
        else:
            self.write_result(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')
            return

        self.process_result(ret, msg)
