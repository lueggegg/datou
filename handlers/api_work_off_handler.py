# -*- coding: utf-8 -*-

import os
from tornado import gen

import error_codes
import type_define
from auto_job_util import UtilAutoJob
from api_job_handler import JobHandler


job_sequence_map = {
    type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY_NEW: {
        type_define.job_sequence_add: type_define.job_sequence_pre_judge,
        type_define.job_sequence_pre_judge: type_define.job_sequence_leader_judge,
        type_define.job_sequence_leader_judge: type_define.job_sequence_hr_record,
    },
    type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY_NEW: {
        type_define.job_sequence_add: type_define.job_sequence_pre_judge,
        type_define.job_sequence_pre_judge: type_define.job_sequence_leader_judge,
        type_define.job_sequence_leader_judge: type_define.job_sequence_via_leader_judge,
        type_define.job_sequence_via_leader_judge: type_define.job_sequence_hr_record,
    },
    type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY_NEW: {
        type_define.job_sequence_add: type_define.job_sequence_pre_judge,
        type_define.job_sequence_pre_judge: type_define.job_sequence_leader_judge,
        type_define.job_sequence_leader_judge: type_define.job_sequence_via_leader_judge,
        type_define.job_sequence_via_leader_judge: type_define.job_sequence_main_leader_judge,
        type_define.job_sequence_main_leader_judge: type_define.job_sequence_hr_record,
    }
}
job_sequence_map[type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY_NEW] = job_sequence_map[type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY_NEW]

class ApiWorkOffHandler(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        ret, msg = (True, '')
        op = self.get_argument_and_check_it('op')
        content = self.get_argument('content', '')
        now = self.now()
        cur_sequence = type_define.job_sequence_add
        complete_sequence = type_define.job_sequence_hr_record
        need_notify = False
        myself = self.account_info['id']
        if op == 'add':
            cur_sequence = type_define.job_sequence_add
            job_type = int(self.get_argument_and_check_it('job_type'))
            self.check_job_type(job_type)
            job_record = {
                'type': job_type,
                'title': self.get_argument_and_check_it('title'),
                'invoker': self.account_info['id'],
                'time': now,
                'mod_time': now,
                'last_operator': self.account_info['id'],
                'cur_path_index': type_define.job_sequence_pre_judge
            }
            job_id = yield self.job_dao.create_new_job(**job_record)
            self.check_result_and_finish_while_failed(job_id, '创建工作流失败')
            half_day = int(self.get_argument_and_check_it('half_day'))
            leave_detail = {
                'job_id': job_id,
                'begin_time': self.get_argument_and_check_it('begin_time'),
                'end_time': self.get_argument_and_check_it('end_time'),
                'half_day': half_day,
                'leave_type': self.get_argument_and_check_it('leave_type'),
                'uid': self.account_info['id'],
            }
            other_type = self.get_argument('other_type', None)
            if other_type:
                leave_detail['extend'] = other_type
            rest_annual = self.get_argument('rest', None)
            if rest_annual is not None:
                rest_annual = int(rest_annual)
                leave_detail['annual_part'] = rest_annual if half_day > rest_annual else half_day
                leave_detail['off_part'] = 0 if half_day <= rest_annual else half_day - rest_annual
                if leave_detail['annual_part'] > 0:
                    annual = yield self.job_dao.query_user_annual_leave(self.account_info['id'])
                    yield self.job_dao.update_user_annual_leave(annual['id'],undetermined=annual['undetermined']+leave_detail['annual_part'])
            yield self.job_dao.add_new_leave_detail(**leave_detail)
        elif op == 'reply':
            job_id = self.get_argument_and_check_it('job_id')
            job_record = yield self.job_dao.query_job_base_info(job_id)
            cur_sequence = job_record['cur_path_index']
        elif op == 'cancel':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_CANCEL)
            leave_detail = yield self.job_dao.query_new_leave_detail(job_id)
            if leave_detail['annual_part'] is not None and leave_detail['annual_part'] > 0:
                annual = yield self.job_dao.query_user_annual_leave(self.account_info['id'])
                yield self.job_dao.update_user_annual_leave(annual['id'], undetermined=annual['undetermined']-leave_detail['annual_part'])
            self.process_result(True, '撤消休假流程')
            return
        elif op == 'reject':
            job_id = self.get_argument_and_check_it('job_id')
            yield self.check_job_mark(job_id)
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_REJECTED)
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
            msg = '拒绝申请'
            job_record = yield self.job_dao.query_job_base_info(job_id)
            cur_sequence = job_record['cur_path_index']
            leave_detail = yield self.job_dao.query_new_leave_detail(job_id)
            if leave_detail['annual_part'] is not None and leave_detail['annual_part'] > 0:
                annual = yield self.job_dao.query_user_annual_leave(self.account_info['id'])
                yield self.job_dao.update_user_annual_leave(annual['id'], undetermined=annual['undetermined']-leave_detail['annual_part'])
        elif op == 'roll':
            self.finish_with_error(1, '数据库异常')
            return
        has_attachment = self.get_argument('has_attachment', 0)
        job_node = {
            'job_id': job_id,
            'time': now,
            'sender_id': self.account_info['id'],
            'content': content,
            'has_attachment': has_attachment,
            'branch_id': cur_sequence,
        }
        node_id = yield self.job_dao.add_job_node(False, **job_node)
        if job_node['has_attachment'] == '1':
            file_list = self.get_argument_and_check_it('file_list')
            file_list = self.loads_json(file_list)
            job_attachment = {'node_id': node_id}
            for path_id in file_list:
                if not path_id:
                    continue
                path_info = yield self.job_dao.query_file_path(path_id)
                job_attachment['name'] = path_info['filename']
                job_attachment['path'] = path_info['path']
                job_attachment['type'] = type_define.TYPE_JOB_ATTACHMENT_NORMAL
                yield self.job_dao.add_node_attachment(**job_attachment)
        self.process_result(ret, msg)

        self.ilog('process after finish ' + op)
        if op == 'reply' or op == 'add':
            if cur_sequence != complete_sequence:
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_PROCESSED, job_record['invoker'])
                job_type = job_record['type']
                next_sequence = job_sequence_map[job_type][cur_sequence]
                if next_sequence in [type_define.job_sequence_hr_record, type_define.job_sequence_pre_judge]:
                    uids = yield self.account_dao.query_account_list(dept_id=22, field_type=type_define.TYPE_ACCOUNT_JUST_ID)
                    for uid in uids:
                        yield self.job_dao.update_job_mark(job_id, uid['id'], type_define.STATUS_JOB_MARK_WAITING)
                elif next_sequence == type_define.job_sequence_leader_judge:
                    util = UtilAutoJob(account_dao=self.account_dao, job_dao=self.job_dao)
                    leader = yield util.get_account_leader(self.account_info['id'], 'dept')
                    yield self.job_dao.update_job_mark(job_id, leader['id'], type_define.STATUS_JOB_MARK_WAITING)
                elif next_sequence == type_define.job_sequence_via_leader_judge:
                    util = UtilAutoJob(account_dao=self.account_dao, job_dao=self.job_dao)
                    leader = yield util.get_account_leader(self.account_info['id'], 'via')
                    yield self.job_dao.update_job_mark(job_id, leader['id'], type_define.STATUS_JOB_MARK_WAITING)
                elif next_sequence == type_define.job_sequence_hr_leader_judge:
                    yield self.job_dao.update_job_mark(job_id, 277, type_define.STATUS_JOB_MARK_WAITING)
                elif next_sequence == type_define.job_sequence_main_leader_judge:
                    yield self.job_dao.update_job_mark(job_id, 212, type_define.STATUS_JOB_MARK_WAITING)
                yield self.job_dao.update_job(job_id, cur_path_index=next_sequence)
            else:
                yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_COMPLETED)
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
                leave_detail = yield self.job_dao.query_new_leave_detail(job_id)
                if leave_detail['annual_part'] is not None and leave_detail['annual_part'] > 0:
                    annual = yield self.job_dao.query_user_annual_leave(self.account_info['id'])
                    yield self.job_dao.update_user_annual_leave(annual['id'], used=annual['used']+leave_detail['annual_part'],
                                                                undetermined=annual['undetermined'] - leave_detail['annual_part'])


    @gen.coroutine
    def check_job_mark(self, job_id):
        job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
        if job_mark and job_mark['status'] != type_define.STATUS_JOB_INVOKED_BY_MYSELF and job_mark['status'] != type_define.STATUS_JOB_MARK_WAITING:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '工作流状态异常，不能操作')