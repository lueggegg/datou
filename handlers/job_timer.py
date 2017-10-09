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
        self.timeout_base = 60
        self.auto_job_timeout = kwargs['auto_job_timeout'] * self.timeout_base
        self.auto_job_extra_timeout = self.auto_job_timeout/3
        self.auto_job_queue = Queue()
        IOLoop.current().call_later(3, self.start_history_tasks)

    @gen.coroutine
    def start_history_tasks(self):
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
                IOLoop.current().call_later((task['time'] - now).seconds, self.auto_job_timeout_cb)
            else:
                IOLoop.current().call_later(self.auto_job_extra_timeout, self.auto_job_timeout_cb)
                time = now + datetime.timedelta(seconds=self.auto_job_extra_timeout)
                yield self.job_dao.update_job_timer_task(task['id'], time=time)

    @gen.coroutine
    def auto_job_timer_start(self, cur_path):
        if not config.enable_job_timer:
            return
        yield self.auto_job_queue.put(cur_path)
        IOLoop.current().call_later(self.auto_job_timeout, self.auto_job_timeout_cb)
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
            sender = yield self.account_dao.query_pure_account('system')
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


    def now(self):
        return datetime.datetime.now()
