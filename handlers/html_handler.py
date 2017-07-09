from base_handler import BaseHandler
from tornado import gen

class HtmlHandler(BaseHandler):

    def post(self, *args, **kwargs):
        self.send_error(404)

    @gen.coroutine
    def get(self, *args, **kwargs):
        st = yield self.verify_user()
        if not st:
            return
        path = self.request.path
        self.render(path[1:], account_info=self.account_info)
