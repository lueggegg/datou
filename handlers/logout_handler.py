from base_handler import BaseHandler

class LogoutHandler(BaseHandler):
    def post(self, *args, **kwargs):
        self.send_error(404)

    def get(self, *args, **kwargs):
        self.clear_token()
        self.redirect_login()
