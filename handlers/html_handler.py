# -*- coding: utf-8 -*-

from base_handler import BaseHandler, HttpClient
from tornado import gen

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
            self.wlog('yc_request to %s from %s' % (path, self.request.remote_ip))
            self.push(self.request.remote_ip)
        try:
            arg = self.request.arguments
            self.render(path[1:], account_info=self.account_info, arg=arg)
        except IOError:
            self.send_error(404)

    @gen.coroutine
    def push(self, ip):
        client = HttpClient()
        client.url('http://whois.pconline.com.cn/ip.jsp?ip=%s' % ip)
        resp = yield client.get()
        extra = {
            "type": -1,
            "job_id": -1,
            'title': ip,
            'content': resp.body.strip().decode('gbk'),
            'sender': 'system'
            }
        self.push_server.push_with_alias("", [250], extra)
