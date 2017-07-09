from base_handler import BaseHandler
import error_codes
from tornado import gen

class EmployeeManageHandler(BaseHandler):

    def post(self, *args, **kwargs):
        self.send_error(404)

    @gen.coroutine
    def get(self, *args, **kwargs):
        st = yield self.verify_user()
        if not st:
            return
        self.render('employee_manage.html', account_info=self.account_info)
