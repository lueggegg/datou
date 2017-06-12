# -*- coding: utf-8 -*-

from base_handler import BaseHandler
import error_codes
from tornado import gen
import codecs
import os
import json

class ApiGetPasswordProtectQuestion(BaseHandler):

    @gen.coroutine
    def _deal_request(self):
        st = yield self.verify_user()
        if not st:
            return
        try:
            self.write_json({'status': 0, 'data': self.psd_question})

        except Exception, e:
            self.write_result(error_codes.EC_SYS_ERROR, '系统错误')

    def post(self, *args, **kwargs):
        self._deal_request()

    @gen.coroutine
    def get(self, *args, **kwargs):
        self.send_error(404)
        # self._deal_request()
