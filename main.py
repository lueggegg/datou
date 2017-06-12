import os

import tornado.web
from tornado import ioloop
import handlers

app = tornado.web.Application([
    (r'/res/(.*)', tornado.web.StaticFileHandler, {'path': "./template/res/"}),
    (r'/', handlers.IndexHandler),
    (r'/index.html', handlers.IndexHandler),
    (r'/login.html', handlers.LoginHandler),
    (r'/logout.html', handlers.LogoutHandler),
    (r'/error.html', handlers.ErrorHandler),
    (r'/personal.html', handlers.PersonalHandler),
    (r'/api/update_account_info', handlers.ApiUpdateAccountInfo),
    (r'/api/update_password_protect_question', handlers.ApiUpdatePasswordPretectQuestion),
    (r'/api/get_password_protect_question', handlers.ApiGetPasswordProtectQuestion),
    (r'/api/update_login_phone', handlers.ApiUpdateLoginPhone),
],
    autoreload=False,
    cookie_secret='a05e6ee50f9f0b5d7cbade2fee456874a',
    template_path=os.path.join(os.path.dirname(__file__), "template"),
)

app.listen(5505, '0.0.0.0')
ioloop.IOLoop.current().start()