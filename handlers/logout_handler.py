from base_handler import BaseHandler
import error_codes

class LogoutHandler(BaseHandler):
    def post(self, *args, **kwargs):
        self.clear_token()
        self.write_result(error_codes.EC_SUCCESS, "logout")

    def get(self, *args, **kwargs):
        self.clear_token()
        self.redirect_login()
