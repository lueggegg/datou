# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler

class ApiFetchMyInfo(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        self.need_redirect_login = False
        if self.account_info:
            self.write_data(self.account_info)
