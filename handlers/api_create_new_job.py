# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
from api_handler import ApiHandler

class ApiCreateNewJob(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        job_info = self.get_argument('job_info', None)
        if not job_info:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
        job_info = self.loads_json(job_info)

        first_node = self.get_argument('node', None)
        if not first_node:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
        first_node = self.loads_json(first_node)
        first_node['time'] = self.now()

        ret = False
        job_id = yield self.job_dao.create_new_job(**job_info)
        if job_id:
            node_id = yield self.job_dao.add_node(**first_node)
            if not node_id:
                yield self.job_dao.delete_job(job_id)
            else:
                ret = True
        if not ret:
            self.write_result(error_codes.EC_SYS_ERROR, '创建工作流失败')

