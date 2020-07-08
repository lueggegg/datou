# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiNoVerifyHandler

import error_codes
import type_define

class ApiQueryJobInfo(ApiNoVerifyHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        job_id = self.get_argument_and_check_it('job_id')
        info_type = self.get_argument_and_check_it('type')

        if info_type == 'node':
            branch_id = self.get_argument('branch_id', None)
            count = self.get_argument('count', None)
            ret = yield self.job_dao.query_job_node_list(job_id, branch_id, count)
            last_node = None
            for item in ret:
                attachment_type = [
                    ['has_attachment', type_define.TYPE_JOB_ATTACHMENT_NORMAL, 'attachment'],
                    ['has_img', type_define.TYPE_JOB_ATTACHMENT_IMG, 'img_attachment'],
                ]
                for _type in attachment_type:
                    if item[_type[0]]:
                        attachment = yield self.job_dao.query_node_attachment_list(item['id'], _type[1])
                        item[_type[2]] = attachment

                last_node = item
            if last_node and last_node['rec_id']:
                rec_account = yield self.account_dao.query_account_by_id(last_node['rec_id'])
                last_node['rec_account'] = rec_account['account']
                last_node['rec_name'] = rec_account['name']
                last_node['rec_dept'] = rec_account['dept']
        elif info_type == 'rec_set':
            set_id = self.get_argument_and_check_it('set_id')
            ret = yield self.job_dao.query_uid_set(set_id)
        elif info_type == 'base':
            ret = yield self.job_dao.query_job_base_info(job_id)
        elif info_type == 'authority':
            base_info = yield self.job_dao.query_job_base_info(job_id)
            if base_info['invoker'] == self.account_info['id']:
                ret = True
            else:
                branch_id = self.get_argument('branch_id', None)
                ret = yield self.job_dao.query_job_mark(job_id, self.account_info['id'], branch_id)
                ret= ret is not None
        else:
            ret = None

        res['data'] = ret

        self.write_json(res)
