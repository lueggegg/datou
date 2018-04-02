# -*- coding: utf-8 -*-

import os
from tornado import gen

import error_codes
import type_define
from auto_job_util import UtilAutoJob

from api_job_handler import JobHandler


class ApiProcessAutoJob(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument_and_check_it('op')
        content = self.get_argument('content', '')
        is_comment = False

        now = self.now()
        ret = True
        need_notify = False
        push_content = None
        msg = ''
        uid_list = []
        if op == 'add':
            job_type = int(self.get_argument_and_check_it('job_type'))
            self.check_job_type(job_type)
            util = UtilAutoJob(account_dao=self.account_dao, job_dao=self.job_dao)
            try:
                uid_list = yield util.generate_uid_path_detail(job_type, self.account_info['id'])
            except Exception, e:
                self.finish_with_error(e.args[0], e.args[1])
            # uid_list = yield self.generate_uid_path_detail(job_type)
            if not uid_list:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '没有后续的路径')
            job_record = {
                'type': job_type,
                'title': self.get_argument_and_check_it('title'),
                'invoker': self.account_info['id'],
                'time': now,
                'mod_time': now,
                'last_operator': self.account_info['id'],
                'cur_path_index': None,
            }
            job_id = yield self.job_dao.create_new_job(**job_record)
            self.check_result_and_finish_while_failed(job_id, '创建工作流失败')
            if self.is_type_of_leave(job_type):
                leave_detail = {
                    'job_id': job_id,
                    'begin_time': self.get_argument_and_check_it('begin_time'),
                    'end_time': self.get_argument_and_check_it('end_time'),
                    'leave_type': self.get_argument_and_check_it('leave_type'),
                }
                if job_type in [type_define.TYPE_JOB_LEAVE_FOR_BORN_NORMAL, type_define.TYPE_JOB_LEAVE_FOR_BORN_LEADER]:
                    leave_detail['weight'] = 1
                half_day = self.get_argument('half_day', None)
                if half_day is not None:
                    leave_detail['half_day'] = half_day
                yield self.job_dao.add_leave_detail(**leave_detail)
        elif op == 'reply':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.check_job_mark(job_id)
            job_record = yield self.job_dao.query_job_base_info(job_id)
            msg = '审批申请'
        elif op == 'cancel':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_CANCEL)
            self.process_result(True, '撤消自动化工作流')
            return
        elif op == 'reject':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.check_job_mark(job_id)
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_REJECTED)
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
            msg = '拒绝申请'
            push_content = '【未通过】'
            need_notify = True
        elif op == 'query_cur':
            job_id = self.get_argument_and_check_it('job_id')
            cur_path_index = self.get_argument_and_check_it('cur_path_index')
            uid_path = yield self.job_dao.get_job_uid_path_detail(job_id, cur_path_index)
            if uid_path['uid']:
                fields = ['uid', 'account', 'dept', 'name']
                account = yield self.account_dao.query_account_by_id(uid_path['uid'])
                account['uid'] = account['id']
                self.write_data([self.abstract_account(account, fields)])
            elif uid_path['set_id']:
                uid_set = yield self.job_dao.query_uid_set(uid_path['set_id'])
                self.write_data(uid_set)
            else:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '路径%s错误' % cur_path_index)
            return
        elif op == 'left_comment':
            msg = "备注请假流程"
            is_comment = True
            job_id = self.get_argument_and_check_it('job_id')
            content = self.get_argument('comment', '')
            half_day = self.get_argument('half_day', None)
            if half_day is not None:
                yield self.job_dao.update_leave_detail(job_id, half_day)
        elif op == 'query_leave_detail':
            job_id = self.get_argument_and_check_it('job_id')
            ret = yield self.job_dao.query_leave_detail(job_id)
            self.write_data(ret)
            return
        else:
            job_id = None
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

        has_attachment = self.get_argument('has_attachment', 0)
        has_img = self.get_argument('has_img', 0)
        job_node = {
            'job_id': job_id,
            'time': now,
            'sender_id': self.account_info['id'],
            'content': content,
            'has_attachment': has_attachment,
            'has_img': has_img
        }
        node_type = self.get_argument('node_type', None)
        if node_type:
            job_node['type'] = node_type
        node_id = yield self.job_dao.add_job_node(is_comment, **job_node)
        if not node_id:
            if op == 'add':
                yield self.job_dao.delete_job(job_id)
            yield self.job_dao.delete_job(job_id)
            self.finish_with_error(error_codes.EC_SYS_ERROR, '创建工作流节点失败')

        if op == 'left_comment':
            job_record = yield self.job_dao.query_job_base_info(job_id)
            filename = 'job_%s_%s.html' % (job_id, job_record['title'].decode('utf-8'))
            dir_path = 'res/download/job_export'
            file_path = self.get_res_file_path(filename, dir_path, True)
            os.remove(file_path)
            self.process_result(True, msg)
            return

        attachment_fields = [
            ['has_attachment', 'file_list', type_define.TYPE_JOB_ATTACHMENT_NORMAL],
            ['has_img', 'img_list', type_define.TYPE_JOB_ATTACHMENT_IMG],
        ]
        for field in attachment_fields:
            if job_node[field[0]] == '1':
                file_list = self.get_argument_and_check_it(field[1])
                file_list = self.loads_json(file_list)
                job_attachment = {'node_id': node_id}
                for path_id in file_list:
                    if not path_id:
                        continue
                    path_info = yield self.job_dao.query_file_path(path_id)
                    job_attachment['name'] = path_info['filename']
                    job_attachment['path'] = path_info['path']
                    job_attachment['type'] = field[2]
                    yield self.job_dao.add_node_attachment(**job_attachment)

        self.process_result(ret, msg)

        if op == 'add':
            yield self.generate_job_path_detail(job_id, uid_list)

        ret = yield self.job_dao.query_job_relative_uid_list(job_id)
        push_alias = ret if ret else []
        if self.account_info['id'] in push_alias:
            push_alias.remove(self.account_info['id'])

        if not need_notify:
            index = job_record['cur_path_index'] + 1 if job_record['cur_path_index'] else 1
            next_path = yield self.job_dao.get_job_uid_path_detail(job_id, index)
            if not next_path:
                yield self.job_dao.update_job(job_id, cur_path_index=None)
                yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_COMPLETED)
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
                need_notify = True
                push_content = u'【已归档】' + self.getContentPart(job_node['content'], 1, 15)
            else:
                if op == 'reply':
                    yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_PROCESSED, job_record['invoker'])
                if next_path['uid']:
                    yield self.job_dao.update_job_mark(job_id, next_path['uid'], type_define.STATUS_JOB_MARK_WAITING)
                elif next_path['set_id']:
                    uid_set = yield self.job_dao.query_uid_set(next_path['set_id'], True)
                    for item in uid_set:
                        yield self.job_dao.update_job_mark(job_id, item['uid'], type_define.STATUS_JOB_MARK_WAITING)
                yield self.job_dao.update_job(job_id, cur_path_index=next_path['order_index'])
                push_content = u'【新回复】' + self.getContentPart(job_node['content'], 1, 15)
                self.job_timer.auto_job_timer_start(next_path)

        if push_content and push_alias:
            extra =  {
                "type": job_record['type'],
                "job_id": job_id,
                'title': job_record['title'],
                'content': push_content,
                'sender': self.account_info['name']
            }
            self.push_server.push_with_alias("", push_alias, extra)

        if need_notify:
            notify_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_JUST_ID,
                                                                    operation_mask=type_define.OPERATION_MASK_QUERY_AUTO_JOB)
            notify_list = [item['id'] for item in notify_list]
            yield self.job_dao.job_notify(job_id, notify_list, type_define.TYPE_JOB_NOTIFY_AUTO_JOB)


    @gen.coroutine
    def generate_job_path_detail(self, job_id, uid_list):
        index = 1
        for item in uid_list:
            if isinstance(item, int):
                yield self.job_dao.add_job_uid_path_detail(job_id, index, uid=item)
            else:
                set_id = yield self.job_dao.create_uid_set()
                yield self.job_dao.add_job_uid_path_detail(job_id, index, set_id=set_id)
                yield self.job_dao.insert_into_uid_set(set_id, item)
            index += 1

    @gen.coroutine
    def check_job_mark(self, job_id):
        job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
        if job_mark and job_mark['status'] != type_define.STATUS_JOB_INVOKED_BY_MYSELF and job_mark['status'] != type_define.STATUS_JOB_MARK_WAITING:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '工作流状态异常，不能回复')


