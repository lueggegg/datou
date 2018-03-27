import jpush
from jpush import common
from jpush.push.core import Push, PushResponse
import logging

from base_handler import MyEncoder, HttpClient

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

    def __init__(self, call_remote=True):
        self.app_key = 'f7430a1c1812e2102d67e1af'
        self.master_secret = 'd2bfa63c88ec21ceea89c228'
        # self._jpush = MyJPush(self.app_key, self.master_secret)
        self._jpush = jpush.JPush(self.app_key, self.master_secret)
        self.call_remote = call_remote

    def call_in_remote_server(self, method, **kwargs):
        logging.info("remote push: %s" % kwargs)
        client = HttpClient()
        client.url("http://localhost:6606").add('op', 'push').add("method", method)
        if kwargs:
            client.add('kwargs', MyEncoder.dumps_json(kwargs))
        client.post()

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

    def push_with_alias(self, msg, alias=None, extra=None):
        if self.call_remote:
            self.call_in_remote_server('push_with_alias', msg=msg, alias=alias, extra=extra)
            return
        push =self. _jpush.create_push()
        push.platform = jpush.all_
        if alias:
            push.audience = jpush.audience({'alias': alias})
        else:
            push.audience = jpush.all_
        android = jpush.android(alert=msg, extras=extra)
        ios = jpush.ios(alert="%s\n%s: %s" % (extra['title'], extra['sender'], extra['content']))
        push.notification = jpush.notification(alert=msg, android=android, ios=ios)
        print (push.payload)
        retry_time = 3
        while retry_time:
            try:
                push.send()
                return
            except:
                retry_time -= 1

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
