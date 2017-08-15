# -*- coding: utf-8 -*-

from tornado import gen
from api_handler import ApiNoVerifyHandler

class AdminOperation(ApiNoVerifyHandler):
    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', None)
        ret = True
        msg = '未定义操作'
        if op == 'clear_job_data':
            ret = yield self.job_dao.clear_all_job_data()
            msg = '清除工作流所有数据'

        if op == 'clear_job_path_data':
            ret = yield self.job_dao.clear_all_job_path_data()
            msg = '清除工作流自动路径'

        self.process_result(ret, msg)