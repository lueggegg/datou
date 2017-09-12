# -*- coding: utf-8 -*-

from tornado import gen
from api_handler import ApiNoVerifyHandler

class AdminOperation(ApiNoVerifyHandler):
    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument('op', None)
        ret = False
        msg = '未定义操作'
        if op == 'init':
            account = yield self.account_dao.query_account('admin')
            if account:
                self.process_result(False, '已经初始化')
                return

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
                    'authority': 1,
                    'portrait': 'default_portrait.png'
                }
                ret = yield self.account_dao.add_account(**account_info)
            msg = '初始化'

        elif op == 'clear_job_data':
            ret = yield self.job_dao.clear_all_job_data()
            msg = '清除工作流所有数据'

        elif op == 'clear_job_path_data':
            ret = yield self.job_dao.clear_all_job_path_data()
            msg = '清除工作流自动路径'

        elif op == 'init_account':
            msg = '初始化员工信息'
            yield self.init_accounts()
            ret = True

        elif op == 'init_report_uid':
            msg = '初始化汇报关系'
            yield self.init_report_uid()
            ret = True

        self.process_result(ret, msg)


    @gen.coroutine
    def init_report_uid(self):
        account_list = yield self.account_dao.query_account_list()
        dept_map = yield self.get_department_map()
        for account in account_list:
            dept = dept_map[account['department_id']]
            while True:
                leader = dept['leader']
                if not leader:
                    break
                if leader != account['id']:
                    yield self.account_dao.update_account(account['id'], report_uid=leader)
                    break
                elif dept['parent']:
                    dept = dept_map[dept['parent']]
                else:
                    break

    @gen.coroutine
    def init_accounts(self):
        dept_list = [
            '公司领导',
            '财务总监',
            '编委',
            '办公室',
            '人事部',
            '总编办',
            '营销策划部',
            '财务室',
            '广告部',
            '工会',
            '专题部',
            '播出部',
            '新闻与编辑部',
            '众创TV',
            '技术部',
            '电台编辑部',
        ]
        dept_map = {}
        for dept in dept_list:
            exist = yield self.account_dao.query_dept(name=dept)
            if exist:
                dept_map[dept] = exist['id']
                continue
            id = yield self.account_dao.add_dept(name=dept)
            dept_map[dept] = id

        filename = self.get_res_file_path('info.txt', '', True)
        fid = open(filename, 'r')
        index = 1000
        psd = self.get_hash('oa123456')
        for line in fid:
            index += 1
            line = line.rstrip()
            info = line.split('\t')
            account_info = {
                'account': 'S%s' % index,
                'name': info[0],
                'department_id': dept_map[info[2]],
                'login_phone': info[1],
                'cellphone': info[1],
                'portrait': 'default_portrait.png',
                'position': '职员',
                'join_date': self.now(),
                'id_card': '12345619900101%s' % index,
                'password': psd,
            }
            yield self.account_dao.add_account(**account_info)

