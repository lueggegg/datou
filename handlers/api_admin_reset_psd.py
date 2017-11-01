# -*- coding: utf-8 -*-

import error_codes
import type_define

from tornado import gen
from api_handler import ApiNoVerifyHandler

class ApiAdminResetPsd(ApiNoVerifyHandler):
    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument_and_check_it('op')

        ret = True
        msg = ''
        if op == 'apply':
            extend = self.get_argument_and_check_it('extend')
            extend_obj = self.loads_json(extend)
            info = {
                'extend': extend,
                'type': type_define.TYPE_JOB_ADMIN_RESET_PSD,
                'invoker': extend_obj['uid'],
                'status': type_define.STATUS_JOB_MARK_WAITING,
            }
            ret = yield self.job_dao.create_admin_job(**info)
            msg = '申请重置密码'
        elif op == 'query':
            yield self.verify_user()
            kwargs = {'type': type_define.TYPE_JOB_ADMIN_RESET_PSD}
            status = self.get_argument('status', None)
            if status is not None:
                kwargs['status'] = status
            count = self.get_argument('count', None)
            offset = self.get_argument('offset', 0)
            ret, total = yield self.job_dao.query_admin_job_list(count, offset, **kwargs)
            for item in ret:
                item['extend'] = self.loads_json(item['extend'])
            self.write_json({
                'status': error_codes.EC_SUCCESS,
                'data': ret,
                'total': total,
            })
            return
        elif op == 'reset':
            yield self.verify_user()
            job_id = self.get_argument_and_check_it('job_id')
            item = yield self.job_dao.query_admin_job(job_id)
            self.check_result_and_finish_while_failed(item)
            if item['status'] == type_define.STATUS_JOB_MARK_WAITING:
                yield self.job_dao.update_admin_job(job_id, status=type_define.STATUS_JOB_MARK_PROCESSED)
            yield self.account_dao.update_account(item['invoker'], password=self.get_hash('oa123456'))
        elif op == 'read':
            yield self.verify_user()
            job_id = self.get_argument_and_check_it('job_id')
            item = yield self.job_dao.query_admin_job(job_id)
            self.check_result_and_finish_while_failed(item)
            if item['status'] == type_define.STATUS_JOB_MARK_WAITING:
                yield self.job_dao.update_admin_job(job_id, status=type_define.STATUS_JOB_MARK_PROCESSED)
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

        self.process_result(ret, msg)