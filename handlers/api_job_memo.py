# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define
from api_job_handler import JobHandler


class ApiJobMemo(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}
        op = self.get_argument('op', 'query')
        job_type = self.get_argument_and_check_it('job_type', None)
        if op == 'query':
            ret = yield self.job_dao.query_job_memo(job_type)
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'update':
            memo = self.get_argument_and_check_it('memo')
            ret = yield self.job_dao.update_job_memo(job_type, memo)
            msg = '更新工作流备注'
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

        self.process_result(ret, msg)
