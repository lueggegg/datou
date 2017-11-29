import jpush
from jpush import common
from jpush.push.core import Push, PushResponse

import logging
from base_handler import MyEncoder

class MyPush(Push):
    def send(self):
        body = MyEncoder.dumps_json(self.payload)
        url = self.url
        response = self._jpush._request('POST', body, url, 'application/json', version=3)
        return PushResponse(response)

class MyJPush(jpush.JPush):
    def create_push(self):
        return MyPush(self)

class JpushServer:

    def __init__(self):
        self.app_key = 'f7430a1c1812e2102d67e1af'
        self.master_secret = 'd2bfa63c88ec21ceea89c228'
        # self._jpush = MyJPush(self.app_key, self.master_secret)
        self._jpush = jpush.JPush(self.app_key, self.master_secret)

    def all(self, msg):
        push = self._jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=msg)
        push.platform = jpush.all_
        try:
            push.send()
        except common.Unauthorized:
            raise common.Unauthorized("Unauthorized")
        except common.APIConnectionException:
            raise common.APIConnectionException("conn")
        except common.JPushFailure:
            print ("JPushFailure")

    def alias(self, msg, alias):
        push = self._jpush.create_push()
        push.audience = jpush.audience({'alias': alias})
        push.platform = jpush.all_
        push.notification = jpush.notification(alert=msg)
        print (push.payload)
        push.send()

    def android(self, msg):
        push =self. _jpush.create_push()
        push.audience = jpush.all_
        push.platform = jpush.all_
        android = jpush.android(alert=msg, priority=1, style=1, alert_type=2,big_text='jjjjjjjjjj', extras={'k1':'v1'})
        ios = jpush.ios(alert="Hello, IOS JPush!", sound="a.caf", extras={'k1': 'v1'})
        push.notification = jpush.notification(alert=msg, android=android, ios=ios)
        print (push.payload)
        push.send()

    def silent(self, msg):
        push = self._jpush.create_push()
        push.audience = jpush.all_
        ios_msg = jpush.ios(alert="Hello, IOS JPush!", badge="+1", extras={'k1': 'v1'}, sound_disable=True)
        android_msg = jpush.android(alert="Hello, android msg")
        push.notification = jpush.notification(alert=msg, android=android_msg, ios=ios_msg)
        push.platform = jpush.all_
        push.send()

    def validate(self, msg):
        push = self._jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=msg)
        push.platform = jpush.all_
        push.send_validate()
