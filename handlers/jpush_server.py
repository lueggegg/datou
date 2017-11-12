import jpush
from jpush import common
import logging
from base_handler import MyEncoder


class JpushServer:

    def __init__(self):
        self.app_key = '9e1c45f02b9e27be18734c23'
        self.master_secret = 'c121ac7ef7a18789822343ed'

        self._jpush = jpush.JPush(self.app_key, self.master_secret)
        self._jpush.set_logging("DEBUG")


    def all(self, msg):
        push = self._jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=msg)
        push.platform = jpush.all_
        try:
            response=push.send()
            logging.debug(MyEncoder.dumps_json(response))
        except common.Unauthorized:
            raise common.Unauthorized("Unauthorized")
        except common.APIConnectionException:
            raise common.APIConnectionException("conn")
        except common.JPushFailure:
            print ("JPushFailure")
        except:
            print ("Exception")
