# -*- coding: utf-8 -*-

import codecs
import re

from tornado import gen

import error_codes
import type_define
from api_handler import ApiNoVerifyHandler
from tornado.template import Loader
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest
from base_handler import HttpClient
from auto_job_util import UtilAutoJob
import datetime

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

        elif op == 'get_account_info':
            account = self.get_argument_and_check_it('account')
            ret = yield self.account_dao.query_account(account)
            self.write_data(ret)
            return

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

        elif op == 'client':
            client = HttpClient()
            resp = client.url("http://localhost:5505/api/query_account_list")\
                .add('operation_mask', 32).add('all_allow', 1).post()
            resp = yield resp
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.write(resp.body)
            self.finish()

        elif op == 'push':
            alert = self.get_argument('msg', 'push test')
            alert = '%s %s' % (alert, self.now())
            func = self.get_argument('func', 'all')
            if func == 'alias':
                alias = self.get_argument_and_check_it('alias')
                alias = self.loads_json(alias)
                self.push_server.alias(alert, alias)
            else:
                exec('self.push_server.%s(alert)' % func)

        elif op == 'push_server':
            extra =  {
                    "type": 1,
                    "job_id": 962,
                    'title': 'hello world',
                    'content': '你们好吗',
                    'sender': '磊哥'
                }
            self.push_server.push_with_alias("", [241, 76, 242], extra)

        elif op == 'test':
            pass
            job_record = yield self.job_dao.execute_sql("select * from job_record where status=1 and sub_type=2 and "
                                "mod_time < '%s' " % (self.now() - datetime.timedelta(days=7),))
            # job_record = yield self.job_dao.execute_sql("select id from job_record where status=1 and "
            #                    "type not in %s and last_operator=250 order by id" % (tuple(UtilAutoJob.get_auto_job_type_list()),))
            print len(job_record)
            for index, job_id in enumerate(job_record):
                job_id = job_id['id']
                # print index, job_id
                # yield self.job_dao.execute_sql("update job_status_mark set status=%s where job_id=%s" % (
                #     type_define.STATUS_JOB_MARK_WAITING, job_id
                # ))
                # yield self.job_dao.execute_sql("update job_node n set n.status=0 where n.id in "
                #     "(select * from (select max(a.id) from job_node a where a.job_id=%s) kk)" % job_id)
                # yield self.job_dao.execute_sql("update job_record set status=%s, mod_time='%s' where id=%s"
                #         % (type_define.STATUS_JOB_PROCESSING, self.now()-datetime.timedelta(days=2), job_id))

                # node = yield self.job_dao.execute_sql("select a.* from job_node a where a.id = "
                #             "(select max(b.id) from job_node b where b.job_id=%s and b.status=1)" % job_id)
                # if not node:
                #     continue
                # node = node[0]
                # yield self.job_dao.execute_sql("update job_record set mod_time='%s', last_operator=%s where id=%s"
                #         % (node['time'], node['sender_id'], job_id))
                # yield self.job_dao.execute_sql("delete from job_notify where job_id=%s and type=%s" %
                #                                (job_id, type_define.TYPE_JOB_NOTIFY_SYS_MSG))
                # yield self.job_dao.execute_sql("update job_status_mark set status=%s where job_id=%s" % (type_define.STATUS_JOB_MARK_PROCESSED, job_id))
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
