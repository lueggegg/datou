# -*- coding: utf-8 -*-

import codecs
import re

from tornado import gen

import error_codes
import type_define
from api_handler import ApiNoVerifyHandler
from tornado.template import Loader


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

        elif op == 'get_account_list':
            ret = yield self.account_dao.query_account_list()
            fields = ['account', 'name', 'dept', 'login_phone']
            labels = ['账号', '姓名', '部门', '登录手机']
            other_fields = [
                ['id_card','身份证'],
                ['position', '职位'],
            ]
            for item in other_fields:
                if self.get_argument(item[0], None):
                    labels.append(item[1])
                    fields.append(item[0])
            result = '\t'.join(labels) + '\n'
            for item in ret:
                result += '\t'.join([item[field] if item[field] else '' for field in fields])
                result += '\n'
            filename = self.get_hash('%s' % self.now()) + '.xlsx'
            path = self.get_res_file_path(filename, 'res/temp', True)
            # fid = open(path, 'w')
            fid = codecs.open(path, 'w', encoding='utf-8')
            result = result.decode('utf-8')
            fid.write(result)
            self.redirect('/res/temp/' + filename)
            fid.close()
            return

        elif op == 'login_account':
            uid = self.get_argument('uid', None)
            account = self.get_argument('account', None)
            account_info = None
            if uid is not None:
                account_info = yield self.account_dao.query_account_by_id(uid)
            elif account is not None:
                account_info = yield self.account_dao.query_account(account)
            else:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            if not account_info:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '用户不存在')
            else:
                self.set_token(account_info['id'], account_info['account'])
                self.redirect_index()

        elif op == 'copy_account':
            src = self.get_argument_and_check_it('src')
            des = self.get_argument_and_check_it('des')
            account_info = yield self.account_dao.query_pure_account(src)
            account_info.pop('id')
            account_info['account'] = des
            account_info['name'] = des
            account_info['login_phone'] = None
            ret = yield self.account_dao.add_account(**account_info)
            msg = '复制员工'

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

        elif op == 'exec_dao':
            msg = '测试dao:'
            dao = self.get_argument_and_check_it('dao')
            func = self.get_argument_and_check_it('func')
            args = self.get_argument('args', '')
            if args:
                args = self.loads_json(args)
                args = ','.join(args)
            todo = 'ret = self.%s.%s(%s)' % (dao, func, args)
            exec todo
            ret = yield ret
            self.write_json({'data': ret})
            return

        elif op == 're_node':
            msg = '替换html标签'
            ret = True
            node_list = yield self.job_dao.query_html_tag_job_node_list()
            for node in node_list:
                content = self.replace_html_content(node['content'])
                yield self.job_dao.update_job_node(node['id'], content=content)

        elif op == 'push':
            self.push_server.all('push test %s' + self.now())

        elif op == 'test':
            pass

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
