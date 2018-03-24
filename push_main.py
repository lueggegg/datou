import os

import tornado.web
from tornado import ioloop
import tornado.options
from tornado.options import define, options
from tornado.web import RequestHandler
from handlers.base_handler import MyEncoder
from handlers.jpush_server import JpushServer

import logging
import traceback

define("port", 6606, int, "Listen port")
define("address", "0.0.0.0", str, "Bind address")
options.parse_command_line()

class PushHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        RequestHandler.__init__(self, application, request, **kwargs)
        self.push_server = JpushServer(False)
        self.retry_times = 3

    def post(self, *args, **kwargs):
        op = self.get_argument("op", None)
        if op == "push":
            logging.debug(MyEncoder.dumps_json(self.request.arguments))
            method_name = self.get_argument('method', None)
            if method_name:
                try:
                    method = getattr(self.push_server, method_name)
                except:
                    logging.error('no method "%s" in push_server' % method_name)
                    return
                kwargs = self.get_argument('kwargs', {})
                if kwargs:
                    kwargs = MyEncoder.loads_json(kwargs)
                index = 0
                while index < self.retry_times:
                    try:
                        index += 1
                        method(**kwargs)
                        break
                    except Exception, e:
                        logging.error(self.dump_exp(e))
        elif op == "test":
            self.push_server.all("hello world")

    def get(self, *args, **kwargs):
        return self.send_error(404)

    def dump_exp(self, e):
        return "exp=\"%s\" trace=\"%s\"" % (str(e), traceback.format_exc())


app = tornado.web.Application([
    (r'/', PushHandler),
]
)

app.listen(options.port, options.address)
ioloop.IOLoop.current().start()