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
            job_record = yield self.job_dao.query_job_base_info(job_id)
            yield self.job_dao.complete_job(job_id, type_define.STATUS_JOB_CANCEL)
            leave_detail = yield self.job_dao.query_new_leave_detail(job_id)
            annual_part = leave_detail['annual_part']
            if annual_part is not None and annual_part != 0 and job_record['sub_type'] != type_define.TYPE_JOB_ROLL_BACK_LEAVE:
                annual = yield self.job_dao.query_user_annual_leave(job_record['invoker'])
                yield self.job_dao.update_user_annual_leave(annual['id'], undetermined=annual['undetermined']-leave_detail['annual_part'])
            if job_record['sub_type'] == type_define.TYPE_JOB_ROLL_BACK_LEAVE:
                yield self.job_dao.update_job(job_id, cur_path_id=0)
            self.process_result(True, '撤消申请流程')
            return
        elif op == 'reject':
            job_id = self.get_argument_and_check_it('job_id')
            job_record = yield self.job_dao.query_job_base_info(job_id)
            yield self.check_job_mark(job_id)
            yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_REJECTED)
            yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_COMPLETED)
            msg = '拒绝申请'
            cur_sequence = job_record['cur_path_index']
            leave_detail = yield self.job_dao.query_new_leave_detail(job_id)
            annual_part = leave_detail['annual_part']
            if annual_part is not None and annual_part != 0 and job_record['sub_type'] != type_define.TYPE_JOB_ROLL_BACK_LEAVE:
                annual = yield self.job_dao.query_user_annual_leave(job_record['invoker'])
                yield self.job_dao.update_user_annual_leave(annual['id'], undetermined=annual['undetermined']-annual_part)
            if job_record['sub_type'] == type_define.TYPE_JOB_ROLL_BACK_LEAVE:
                yield self.job_dao.update_job(job_id, cur_path_id=0)
        elif op == 'roll':
            job_id = self.get_argument_and_check_it('job_id')
            job_record = yield self.job_dao.query_job_base_info(job_id)
            leave_detail = yield self.job_dao.query_new_leave_detail(job_id)
            half_day = int(self.get_argument_and_check_it('half_day'))
            if half_day > leave_detail['half_day']:
                self.finish_with_error(3, '撤销天数不能大于请假天数')
            roll_record = {
                'type': job_record['type'],
                'sub_type': type_define.TYPE_JOB_ROLL_BACK_LEAVE,
                'title': '销假申请',
                'invoker': self.account_info['id'],
                'time': now,
                'mod_time': now,
                'last_operator': self.account_info['id'],
                'cur_path_index': type_define.job_sequence_pre_judge,
                'cur_path_id': job_id,
            }
            roll_id = yield self.job_dao.create_new_job(**roll_record)
            cur_sequence = type_define.job_sequence_add
            yield self.job_dao.update_job(job_id, cur_path_id=roll_id)
            roll_detail = {
                'job_id': roll_id,
                'begin_time': self.get_argument_and_check_it('begin_time'),
                'end_time': self.get_argument_and_check_it('end_time'),
                'half_day': -half_day,
                'leave_type': leave_detail['leave_type'],
                'uid': self.account_info['id'],
            }
            if leave_detail['off_part'] > 0 or leave_detail['annual_part'] > 0:
                if leave_detail['off_part'] >= half_day:
                    roll_detail['off_part'] = -half_day
                else:
                    roll_detail['off_part'] = leave_detail['off_part']
                    roll_detail['annual_part'] = leave_detail['off_part'] - half_day
                yield self.job_dao.add_new_leave_detail(**roll_detail)
            job_id = roll_id

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
        if op == 'roll':
            self.write_data(job_id)
            self.finish()
        else:
            self.process_result(ret, msg)

        self.ilog('process after finish ' + op)
        if op == 'reply' or op == 'add' or op == 'roll':
            stop = cur_sequence == complete_sequence
            if not stop:
                yield self.job_dao.update_job_all_mark(job_id, type_define.STATUS_JOB_MARK_PROCESSED, job_record['invoker'])
                job_type = job_record['type']
                invoker = job_record['invoker']
                while not stop:
                    stop = True
                    next_sequence = job_sequence_map[job_type][cur_sequence]
                    if next_sequence in [type_define.job_sequence_hr_record, type_define.job_sequence_pre_judge]:
                        uids = yield self.account_dao.query_account_list(dept_id=22, field_type=type_define.TYPE_ACCOUNT_JUST_ID)
                        for uid in uids:
                            yield self.job_dao.update_job_mark(job_id, uid['id'], type_define.STATUS_JOB_MARK_WAITING)
                    elif next_sequence == type_define.job_sequence_leader_judge:
                        util = UtilAutoJob(account_dao=self.account_dao, job_dao=self.job_dao)
                        leader = yield util.get_account_leader(invoker, 'dept')
                        if leader['id'] == invoker:
                            stop = False
                            cur_sequence = next_sequence
                            job_node = {
                                'job_id': job_id,
                                'time': now,
                                'sender_id': 250,
                                'content': '{申请人为部门负责人，跳过此步骤}',
                                'branch_id': cur_sequence,
                            }
                            node_id = yield self.job_dao.add_job_node(False, **job_node)
                            continue
                        elif invoker in [121, 122, 138]:
                            stop = False
                            cur_sequence = next_sequence
                            job_node = {
                                'job_id': job_id,
                                'time': now,
                                'sender_id': 250,
                                'content': '{该职位跳过此步骤}',
                                'branch_id': cur_sequence,
                            }
                            node_id = yield self.job_dao.add_job_node(False, **job_node)
                            continue
                        else:
                            yield self.job_dao.update_job_mark(job_id, leader['id'], type_define.STATUS_JOB_MARK_WAITING)
                    elif next_sequence == type_define.job_sequence_via_leader_judge:
                        util = UtilAutoJob(account_dao=self.account_dao, job_dao=self.job_dao)
                        leader = yield util.get_account_leader(invoker, 'via')
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
                annual_part = leave_detail['annual_part']
                if annual_part is not None and annual_part != 0:
                    annual = yield self.job_dao.query_user_annual_leave(job_record['invoker'])
                    undetermined = 0 if job_record['sub_type'] == type_define.TYPE_JOB_ROLL_BACK_LEAVE else annual_part
                    yield self.job_dao.update_user_annual_leave(annual['id'], used=annual['used']+annual_part,
                                                                undetermined=annual['undetermined'] - undetermined)


    @gen.coroutine
    def check_job_mark(self, job_id):
        job_mark = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
        if job_mark and job_mark['status'] != type_define.STATUS_JOB_INVOKED_BY_MYSELF and job_mark['status'] != type_define.STATUS_JOB_MARK_WAITING:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '工作流状态异常，不能操作')
