# -*- coding: utf-8 -*-

from base_handler import BaseHandler, HttpClient
from tornado import gen

class NoLoginHandler(BaseHandler):

    def post(self, *args, **kwargs):
        self.send_error(404)

    @gen.coroutine
    def get(self, *args, **kwargs):
        path = self.request.path
        try:
            yield self.verify_user(redirect=False)
            arg = self.request.arguments
            target = path[1:]
            self.render(target, account_info=self.account_info, arg=arg)
        except IOError:
            self.send_error(404)