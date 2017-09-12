# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define

from api_job_handler import JobHandler


class ApiProcessAutoJob(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument_and_check_it('op')
        job_type = int(self.get_argument_and_check_it('job_type'))
        self.check_job_type(job_type)
        content = self.get_argument('content', '')

        now = self.now()
        path = None
        if op == 'add':
            path = yield  self.job_dao.query_first_job_auto_path(job_type)
            if not path:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置自动化流程')
            job_record = {
                'type': job_type,
                'title': self.get_argument_and_check_it('title'),
                'invoker': self.account_info['id'],
                'time': now,
                'mod_time': now,
                'last_operator': self.account_info['id'],
            }
            job_id = yield self.job_dao.create_new_job(**job_record)
            self.check_result_and_finish_while_failed(job_id, '创建工作流失败')
        elif op == 'reply':
            job_id = self.get_argument_and_check_it('job_id')
            job_record = yield self.job_dao.query_job_base_info(job_id)
            if job_record['report_status']:
                path = yield self.job_dao.query_job_auto_path(job_type, pre_path_id=job_record['cur_path_id'])
            else:
                path = yield self.job_dao.query_first_job_auto_path(job_type)
        elif op == 'cancel':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_CANCEL)
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
            self.process_result(True, '撤消自动化工作流')
            return
        elif op == 'reject':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_REJECTED)
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
        else:
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
        job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
        if job_mark and job_mark['status'] != type_define.STATUS_JOB_INVOKED_BY_MYSELF and job_mark['status'] != type_define.STATUS_JOB_MARK_WAITING:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '该工作流已经被审阅或撤回')
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

        if op == 'reject':
            self.process_result(True, '自动化工作流')
            return

        if not path:
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_COMPLETED)
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
        else:
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_PROCESSED)
            mark_done = False
            to_leader = path['to_leader']
            report_complete = False
            if to_leader:
                if to_leader == type_define.TYPE_REPORT_TO_LEADER_TILL_CHAIR:
                    report_complete = self.account_info['authority'] <= type_define.AUTHORITY_CHAIR_LEADER
                elif to_leader == type_define.TYPE_REPORT_TO_LEADER_TILL_VIA:
                    report_complete = self.account_info['authority'] <= type_define.AUTHORITY_VIA_LEADER
                elif to_leader == type_define.TYPE_REPORT_TO_LEADER_TILL_DEPT:
                    report_complete = self.account_info['authority'] <= type_define.AUTHORITY_DEPT_LEADER
                if not report_complete:
                    next_rec = self.account_info['report_uid']
                    if not next_rec:
                        self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置汇报关系，发送失败')
                    else:
                        yield self.job_dao.update_job_mark(job_id, next_rec, type_define.STATUS_JOB_MARK_WAITING)
                        mark_done = True
                else:
                    yield self.job_dao.update_job(job_id, report_status=1)
                    if path['next_path_id']:
                        path = yield self.job_dao.query_job_auto_path(job_type, id=path['next_path_id'])
                    else:
                        yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
                        mark_done = True
            if not mark_done:
                for detail in path['detail']:
                    if detail['uid']:
                        yield self.job_dao.update_job_mark(job_id, detail['uid'], type_define.STATUS_JOB_MARK_WAITING)
                    elif detail['dept_id']:
                        account_list = yield self.account_dao.query_account_list(dept_id=detail['dept_id'])
                        for account in account_list:
                            yield self.job_dao.update_job_mark(job_id, account['id'], type_define.STATUS_JOB_MARK_WAITING)
            yield self.job_dao.update_job(job_id, cur_path_id=path['id'])

        self.process_result(True, '自动化工作流')
