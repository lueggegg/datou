# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define

from api_job_handler import JobHandler


class ApiProcessAutoJob(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        job_type = int(self.get_argument_and_check_it('job_type'))
        op = self.get_argument_and_check_it('op')
        self.check_job_type(job_type)
        content = self.get_argument('content', '')

        now = self.now()
        ret = True
        need_notify = False
        msg = ''
        uid_list = []
        if op == 'add':
            uid_list = yield self.generate_uid_path_detail(job_type)
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
            need_notify = True
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
        node_id = yield self.job_dao.add_job_node(**job_node)
        if not node_id:
            if op == 'add':
                yield self.job_dao.delete_job(job_id)
            yield self.job_dao.delete_job(job_id)
            self.finish_with_error(error_codes.EC_SYS_ERROR, '创建工作流节点失败')

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
                    path_info = yield self.job_dao.query_file_path(path_id)
                    job_attachment['name'] = path_info['filename']
                    job_attachment['path'] = path_info['path']
                    job_attachment['type'] = field[2]
                    yield self.job_dao.add_node_attachment(**job_attachment)

        self.process_result(ret, msg)

        if op == 'add':
            yield self.generate_job_path_detail(job_id, uid_list)

        if not need_notify:
            index = job_record['cur_path_index'] + 1 if job_record['cur_path_index'] else 1
            next_path = yield self.job_dao.get_job_uid_path_detail(job_id, index)
            if not next_path:
                yield self.job_dao.update_job(job_id, cur_path_index=None)
                yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_COMPLETED)
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
                need_notify = True
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
                self.job_timer.auto_job_timer_start(next_path)

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
    def generate_uid_path_detail(self, job_type):
        path = yield self.job_dao.query_first_job_auto_path(job_type)
        if not path:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置路径')
        uid = self.account_info['id']
        uid_list = []
        while path:
            if path['to_leader'] == type_define.TYPE_REPORT_TO_LEADER_TILL_DEPT:
                leader = yield self.get_account_leader(uid, 'dept')
                uid_list.append(leader['id'])
            elif path['to_leader'] == type_define.TYPE_REPORT_TO_LEADER_TILL_VIA:
                leader_list = yield self.get_account_leader(uid, 'via', True)
                uid_list.extend(leader_list)
            elif path['to_leader'] == type_define.TYPE_REPORT_TO_LEADER_TILL_CHAIR:
                leader_list = yield self.get_account_leader(uid, 'chair', True)
                uid_list.extend(leader_list)
            elif path['to_leader'] in [type_define.TYPE_REPORT_CONTINUE_TILL_VIA, type_define.TYPE_REPORT_CONTINUE_TILL_CHAIR]:
                via = yield self.get_account_leader(uid, 'via')
                uid_list.append(via['id'])
                if path['to_leader'] == type_define.TYPE_REPORT_CONTINUE_TILL_CHAIR and via['authority'] > type_define.AUTHORITY_CHAIR_LEADER:
                    if not via['report_uid']:
                        self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置最高领导')
                    uid_list.append(via['report_uid'])
            elif path['to_leader'] == 0:
                uid_set = set()
                for detail in path['detail']:
                    if detail['uid']:
                        uid_set.add(detail['uid'])
                    elif detail['dept_id']:
                        account_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_JUST_ID, dept_id=detail['dept_id'])
                        for account in account_list:
                            uid_set.add(account['id'])
                size = len(uid_set)
                if size == 1:
                    uid_list.append(uid_set.pop())
                elif size > 1:
                    uid_list.append(uid_set)
            else:
                self.finish_with_error(error_codes.EC_SYS_ERROR, 'invalid parameter: path["to_leader"]')

            if path['next_path_id']:
                path = yield self.job_dao.query_job_auto_path(job_type, id=path['next_path_id'])
            else:
                path = None
        self.del_duplicate(uid_list)
        if uid in uid_list:
            uid_list.remove(uid)
        raise gen.Return(uid_list)

    def del_duplicate(self, uid_list):
        eval_list = []
        uid_list.reverse()
        while uid_list:
            item = uid_list.pop()
            eval_list.append({'data': item, 'valid': True})
        single_set = set()
        multi_list = []
        for obj in eval_list:
            item = obj['data']
            if isinstance(item, int):
                if item in single_set:
                    obj['valid'] = False
                else:
                    single_set.add(item)
            else:
                multi_list.append(obj)
        for obj in multi_list:
            for uid in single_set:
                if uid in obj['data']:
                    obj['valid'] = False
        for obj in eval_list:
            if obj['valid']:
                uid_list.append(obj['data'])

    @gen.coroutine
    def check_job_mark(self, job_id):
        job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
        if job_mark and job_mark['status'] != type_define.STATUS_JOB_INVOKED_BY_MYSELF and job_mark['status'] != type_define.STATUS_JOB_MARK_WAITING:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '该工作流已经被审阅或撤回')


