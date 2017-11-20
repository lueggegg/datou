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
        self.app_key = '9e1c45f02b9e27be18734c23'
        self.master_secret = 'c121ac7ef7a18789822343ed'
        # self._jpush = MyJPush(self.app_key, self.master_secret)
        self._jpush = jpush.JPush(self.app_key, self.master_secret)

    def all(self, msg):
        push = self._jpush.create_push()
        push.audience = jpush.all_
        push.notification = jpush.notification(alert=msg)
        push.platform = jpush.all_
        try:
            response=push.send()
        except common.Unauthorized:
            raise common.Unauthorized("Unauthorized")
        except common.APIConnectionException:
            raise common.APIConnectionException("conn")
        except common.JPushFailure:
            print ("JPushFailure")


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
