# -*- coding: utf-8 -*-

import logging

from tornado import gen
from api_handler import ApiHandler

import error_codes
import type_define

class ApiQueryJobInfo(ApiHandler):
    @gen.coroutine
    def _real_deal_request(self):
        res = {"status": error_codes.EC_SUCCESS}
        job_id = self.get_argument_and_check_it('job_id')
        info_type = self.get_argument_and_check_it('type')

        if info_type == 'node':
            dept_map = yield self.get_department_map()
            ret = yield self.job_dao.query_job_node_list(job_id)
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

                item['dept'] = dept_map[item['department_id']]['name']
                last_node = item
            if last_node and last_node['rec_id']:
                rec_account = yield self.account_dao.query_account_by_id(last_node['rec_id'])
                last_node['rec_account'] = rec_account['account']
                last_node['rec_name'] = rec_account['name']
                last_node['rec_dept'] = rec_account['dept']
        elif info_type == 'base':
            ret = yield self.job_dao.query_job_base_info(job_id)
        elif info_type == 'authority':
            ret = yield self.job_dao.query_job_mark(job_id, self.account_info['id'])
            ret= ret is not None
        else:
            ret = None

        res['data'] = ret

        self.write_json(res)
