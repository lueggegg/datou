# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define

class UtilAutoJob:
    def __init__(self, **kwargs):
        self.account_dao = kwargs['account_dao']
        self.job_dao = kwargs['job_dao']

    @staticmethod
    def get_auto_job_type_list():
        return [
            type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY_NEW,
            type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY_NEW,
            type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY_NEW,
            type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY_NEW,
            type_define.TYPE_JOB_HR_RESIGN,
            type_define.TYPE_JOB_FINANCIAL_PURCHASE,
        ]

    def finish_with_error(self, err, msg):
        raise Exception(err, msg)

    @gen.coroutine
    def generate_uid_path_detail(self, job_type, invoker):
        path = yield self.job_dao.query_first_job_auto_path(job_type)
        if not path:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置路径')
        uid_list = []
        while path:
            if path['to_leader'] == type_define.TYPE_REPORT_TO_LEADER_TILL_DEPT:
                leader = yield self.get_account_leader(invoker, 'dept')
                uid_list.append(leader['id'])
            elif path['to_leader'] == type_define.TYPE_REPORT_TO_LEADER_TILL_VIA:
                leader_list = yield self.get_account_leader(invoker, 'via', True)
                uid_list.extend(leader_list)
            elif path['to_leader'] == type_define.TYPE_REPORT_TO_LEADER_TILL_CHAIR:
                leader_list = yield self.get_account_leader(invoker, 'chair', True)
                uid_list.extend(leader_list)
            elif path['to_leader'] in [type_define.TYPE_REPORT_CONTINUE_TILL_VIA, type_define.TYPE_REPORT_CONTINUE_TILL_CHAIR]:
                via = yield self.get_account_leader(invoker, 'via')
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

        self.__del_duplicate(uid_list, invoker)
        raise gen.Return(uid_list)

    @gen.coroutine
    def get_account_leader(self, uid, level, need_list=False):
        if level not in ['dept', 'via', 'chair']:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '系统错误')

        current_account = yield self.account_dao.query_account_by_id(uid)
        if current_account['authority'] in [type_define.AUTHORITY_CHAIR_LEADER, type_define.AUTHORITY_VIA_LEADER]:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '领导不适用此接口')

        need_authority = None
        if level == 'dept':
            need_authority = type_define.AUTHORITY_DEPT_LEADER
        elif level == 'via':
            need_authority = type_define.AUTHORITY_VIA_LEADER
        elif level == 'chair':
            need_authority = type_define.AUTHORITY_CHAIR_LEADER
        count = 5
        leader_list = []
        while True:
            authority = current_account['authority']
            if authority > type_define.AUTHORITY_ADMIN and authority <= type_define.AUTHORITY_DEPT_LEADER:
                leader_list.append(current_account['id'])
            if authority > type_define.AUTHORITY_ADMIN and authority <= need_authority:
                break
            if not current_account['report_uid']:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '未设置汇报关系')
            current_account = yield self.account_dao.query_account_by_id(current_account['report_uid'])
            count -= 1
            if count == 0:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '遍历汇报关系出错：层次过多')
        raise gen.Return(leader_list if need_list else current_account)

    def __del_duplicate(self, uid_list, invoker):
        eval_list = []
        uid_list.reverse()
        while uid_list:
            item = uid_list.pop()
            eval_list.append({'data': item, 'valid': True})
        single_set = set([invoker])
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
