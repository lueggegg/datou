# -*- coding: utf-8 -*-

from base_handler import BaseHandler
from tornado import gen, escape

class HtmlHandler(BaseHandler):

    def post(self, *args, **kwargs):
        self.send_error(404)

    @gen.coroutine
    def get(self, *args, **kwargs):
        path = self.request.path
        if path[1:4] != 'yc_':
            st = yield self.verify_user()
            if not st:
                return
        else:
            self.wlog('yc_request from %s' % self.request.remote_ip)
        try:
            arg = self.request.arguments
            self.render(path[1:], account_info=self.account_info, arg=arg)
        except IOError:
            self.send_error(404)
