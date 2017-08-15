# -*- coding: utf-8 -*-

from tornado import gen
from api_handler import ApiNoVerifyHandler

class AdminOperation(ApiNoVerifyHandler):
    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', None)
        ret = True
        msg = '未定义操作'
        if op == 'init':
            dept_info = {
                'name': '后台',
                'status': 2,
            }
            dept_id = yield self.account_dao.add_dept(**dept_info)
            ret = False
            if dept_id:
                account_info = {
                    'account': 'admin',
                    'name': '超级管理员',
                    'password': self.get_hash(self.get_argument_and_check_it('password')),
                    'department_id': dept_id,
                    'join_date': self.now(),
                    'id_card': '1234561999909091234',
                    'position': '大总管',
                }
                ret = yield self.account_dao.add_account(**account_info)
            msg = '初始化'

        elif op == 'clear_job_data':
            ret = yield self.job_dao.clear_all_job_data()
            msg = '清除工作流所有数据'

        elif op == 'clear_job_path_data':
            ret = yield self.job_dao.clear_all_job_path_data()
            msg = '清除工作流自动路径'

        self.process_result(ret, msg)