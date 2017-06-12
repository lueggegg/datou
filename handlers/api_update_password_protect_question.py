# -*- coding: utf-8 -*-

from base_handler import BaseHandler
import error_codes
from tornado import gen
import codecs
import os
import json

class ApiUpdatePasswordPretectQuestion(BaseHandler):

    @gen.coroutine
    def _deal_request(self):
        st = yield self.verify_user()
        if not st:
            return
        try:
            data = self.get_argument('question_info', None)
            if not data:
                self.write_result(error_codes.EC_ARGUMENT_ERROR, '参数错误')
                return
            question_info = self.loads_json(data)
            if self.psd_question:
                for key in question_info:
                    self.psd_question[key] = question_info[key]
            else:
                self.psd_questions[str(self.account_info['id'])] = question_info
            fid = codecs.open(os.path.join(os.path.dirname(__file__), "psd_question.txt"), 'w', 'utf8')
            fid.write(json.dumps(self.psd_questions, ensure_ascii=False, encoding='utf8'))
            fid.close()
            self.write_result(error_codes.EC_SUCCESS)

        except Exception, e:
            self.write_result(error_codes.EC_SYS_ERROR, '系统错误')

    def post(self, *args, **kwargs):
        self._deal_request()

    @gen.coroutine
    def get(self, *args, **kwargs):
        self.send_error(404)
