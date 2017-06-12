from base_handler import BaseHandler
import error_codes
from tornado import gen

class IndexHandler(BaseHandler):

    def post(self, *args, **kwargs):
        self.send_error(404)

    @gen.coroutine
    def get(self, *args, **kwargs):
        st = yield self.verify_user()
        if not st:
            return
        self.render('index.html', account_info=self.account_info)
