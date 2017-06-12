from base_handler import BaseHandler

class ErrorHandler(BaseHandler):

    def get(self, *args, **kwargs):
        self.render('error.html')

    def post(self, *args, **kwargs):
        self.send_error(500)
