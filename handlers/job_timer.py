# -*- coding: utf-8 -*-

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue

import datetime
import type_define, config

class JobTimer:
    __instance__ = None

    def __init__(self, **kwargs):
        JobTimer.__instance__ = self
        self.account_dao = kwargs['account_dao']
        self.job_dao = kwargs['job_dao']
        self.config_dao = kwargs['config_dao']
        self.timeout_base = 60
        self.auto_job_timeout = kwargs['auto_job_timeout'] * self.timeout_base
        self.auto_job_extra_timeout = self.auto_job_timeout/3
        self.auto_job_queue = Queue()
        self.total_seconds = 86400
        self.system = None
        self.daily_task_monment = datetime.timedelta(hours=6, minutes=0)
        self.call_later(3, self.start)

    def call_later(self, delay, callback):
        IOLoop.current().call_later(delay, callback)

    @gen.coroutine
    def start(self):
        self.start_history_tasks()
        left = self.next_daily_task_left_seconds()
        self.call_later(left, self.daily_task)

    @gen.coroutine
    def start_history_tasks(self):
        self.system = yield self.account_dao.query_pure_account('system')
        if not config.enable_job_timer:
            return
        task_list = yield self.job_dao.query_job_timer_task_list()
        now = self.now()
        for task in task_list:
            job_id = task['job_id']
            job_record = yield self.job_dao.query_job_base_info(job_id)
            cur_path = yield self.job_dao.get_job_uid_path_detail(job_id, job_record['cur_path_index'])
            yield self.auto_job_queue.put(cur_path)
            if task['time'] > now:
                self.call_later((task['time'] - now).seconds, self.auto_job_timeout_cb)
            else:
                self.call_later(self.auto_job_extra_timeout, self.auto_job_timeout_cb)
                time = now + datetime.timedelta(seconds=self.auto_job_extra_timeout)
                yield self.job_dao.update_job_timer_task(task['id'], time=time)

    @gen.coroutine
    def auto_job_timer_start(self, cur_path):
        if not config.enable_job_timer:
            return
        yield self.auto_job_queue.put(cur_path)
        self.call_later(self.auto_job_timeout, self.auto_job_timeout_cb)
        time = self.now() + datetime.timedelta(seconds=self.auto_job_timeout)
        task = yield self.job_dao.query_job_timer_task(cur_path['job_id'])
        if task:
            yield self.job_dao.update_job_timer_task(task['id'], time=time)
        else:
            yield self.job_dao.add_job_timer_task(job_id=cur_path['job_id'], time=time)

    @gen.coroutine
    def auto_job_timeout_cb(self):
        cur_path = yield self.auto_job_queue.get()
        job_id = cur_path['job_id']
        job_record = yield self.job_dao.query_job_base_info(job_id)
        if job_record['cur_path_index'] == cur_path['order_index']:
            # auto job timeout
            sender = self.system
            job_node = {
                'job_id': job_id,
                'time': self.now(),
                'type': type_define.TYPE_JOB_NODE_TIMEOUT,
                'sender_id': sender['id']
            }
            msg = '<div><span>【以下员工，超时未处理该工作流：】</span></div>'
            if cur_path['uid']:
                account = yield self.account_dao.query_account_by_id(cur_path['uid'])
                msg += '<div>　　%s　　%s　　%s</div>' % (account['dept'], account['account'], account['name'])
            elif cur_path['set_id']:
                uid_set = yield self.job_dao.query_uid_set(cur_path['set_id'], True)
                uid_list = [item['uid'] for item in uid_set]
                accounts = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_SAMPLE, uid_list=uid_list)
                for account in accounts:
                    msg += '<div>　　%s　　%s　　%s</div>' % (account['dept'], account['account'], account['name'])
            job_node['content'] = '{%s}' % msg
            yield self.job_dao.add_job_node(**job_node)
            next_path = yield self.job_dao.get_job_uid_path_detail(job_id, cur_path['order_index']+1)
            need_notify = False
            if not next_path:
                yield self.job_dao.del_job_timer_task(job_id)
                yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_COMPLETED)
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
                need_notify = True
            else:
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_PROCESSED,
                                                       job_record['invoker'])
                if next_path['uid']:
                    yield self.job_dao.update_job(job_id, cur_path_index=None)
                    yield self.job_dao.update_job_mark(job_id, next_path['uid'], type_define.STATUS_JOB_MARK_WAITING)
                elif next_path['set_id']:
                    uid_set = yield self.job_dao.query_uid_set(next_path['set_id'], True)
                    for item in uid_set:
                        yield self.job_dao.update_job_mark(job_id, item['uid'], type_define.STATUS_JOB_MARK_WAITING)
                yield self.job_dao.update_job(job_id, cur_path_index=next_path['order_index'])
                self.auto_job_timer_start(next_path)
            if need_notify:
                notify_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_JUST_ID,
                                                                        operation_mask=type_define.OPERATION_MASK_QUERY_AUTO_JOB)
                notify_list = [item['id'] for item in notify_list]
                yield self.job_dao.job_notify(job_id, notify_list, type_define.TYPE_JOB_NOTIFY_AUTO_JOB)


    @gen.coroutine
    def daily_task(self):
        self.call_later(self.total_seconds, self.daily_task)
        self.generate_birthday_wishes()

    @gen.coroutine
    def generate_birthday_wishes(self):
        print 'birthday wishes: %s' % self.now()
        account_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_BIRTHDAY, birthday=self.today())
        if not account_list:
            return
        birthday_config = yield self.config_dao.query_common_config(type_define.TYPE_CONFIG_BIRTHDAY_WISHES)
        config = {}
        for item in birthday_config:
            if item['key_id'] == type_define.TYPE_CONFIG_KEY_BIRTHDAY_WISHES_TITLE:
                config['title'] = item['label']
            elif item['key_id'] == type_define.TYPE_CONFIG_KEY_BIRTHDAY_WISHES_CONTENT:
                config['content'] = item['label']
            elif item['key_id'] == type_define.TYPE_CONFIG_KEY_BIRTHDAY_WISHES_IMG:
                config['img'] = item['label']
        job_record = {
            'time': self.now(),
            'title': config['title'],
            'type': type_define.TYPE_JOB_SYSTEM_MSG,
            'sub_type': type_define.TYPE_JOB_SYSTEM_MSG_SUB_TYPE_BIRTHDAY,
            'invoker': self.system['id'],
            'last_operator': self.system['id'],
            'status': type_define.STATUS_JOB_COMPLETED,
        }
        job_node = {
            'sender_id': self.system['id'],
            'time': self.now(),
            'has_img': 1 if config['img'] != 'invalid' else 0,
        }
        match_fields = ['name', 'position']
        for account in account_list:
            job_id = yield self.job_dao.create_new_job(**job_record)
            job_node['job_id'] = job_id
            job_node['rec_id'] = account ['id']
            content = config['content']
            for field in match_fields:
                content = content.replace('{*%s*}'%field, '{*%s*}' % account[field])
            job_node['content'] = content
            node_id = yield self.job_dao.add_job_node(**job_node)
            if job_node['has_img']:
                attachment = {
                    'node_id': node_id,
                    'type': type_define.TYPE_JOB_ATTACHMENT_IMG,
                    'path': config['img'],
                    'name': 'null'
                }
                yield self.job_dao.add_node_attachment(**attachment)
            yield self.job_dao.update_job_mark(job_id, account['id'], type_define.STATUS_JOB_MARK_SYS_MSG)
            yield self.job_dao.add_notify_item(job_id, account['id'], type_define.TYPE_JOB_NOTIFY_SYS_MSG)

    def next_daily_task_left_seconds(self):
        now = self.now()
        t = now.time()
        now_seconds = (3600*t.hour + 60*t.minute + t.second)
        target_seconds = self.daily_task_monment.total_seconds()
        return (target_seconds + self.total_seconds - now_seconds) % self.total_seconds

    def now(self):
        return datetime.datetime.now()

    def today(self):
        return datetime.date.today()

