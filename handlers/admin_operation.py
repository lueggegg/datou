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

        elif op == 'annual':
            yield self.init_annual()

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
    def init_annual(self):
        us = [('\xe6\x9e\x97\xe6\xa5\xa0', '1989'),
              ('\xe7\x8e\x8b\xe7\xa7\x8b', '1987'),
              ('\xe5\xbb\x96\xe5\xb2\xb1\xe5\xb2\xb3', '2003'),
              ('\xe8\x8b\x8f\xe5\x9b\xbd\xe6\xa2\x81', '1998'),
              ('\xe5\xbc\xa0\xe6\xb5\xb7\xe7\x87\x95', '1982'),
              ('\xe8\xb0\xa2\xe6\xac\xa3', '1988'),
              ('\xe9\x99\x88\xe5\xae\x87\xe7\xbf\x94', '1990'),
              ('\xe8\x91\x9b\xe9\x80\xb8\xe9\xa3\x9e', '1998'),
              ('\xe5\x8f\xb2\xe5\x8d\xab\xe5\x85\xb5', '1983'),
              ('\xe6\x96\xb9\xe6\xb7\x91\xe6\x95\x8f', '2001'),
              ('\xe5\x90\xb4\xe6\xb5\xb7\xe9\x9b\x84', '2002'),
              ('\xe8\xa9\xb9\xe9\x9f\xb5\xe7\x90\xb4', '2006'),
              ('\xe8\x82\x96\xe5\xb7\xa7\xe4\xba\x91', '2014'),
              ('\xe6\xb8\xa9\xe5\x8d\x8e\xe5\xa8\x9f', '2008'),
              ('\xe4\xb8\x81\xe5\x85\xbb\xe4\xb9\x90', '2004'),
              ('\xe6\x9b\xbe\xe5\x8d\xab\xe6\x96\xb0', '2000'),
              ('\xe6\x88\xb4\xe6\x96\x87\xe5\xbf\xa0', '2004'),
              ('\xe5\xae\x8b\xe8\xbf\x9c\xe5\x9f\xba', '2005'),
              ('\xe5\x88\x98\xe8\xa5\xbf\xe9\x87\x91', '1983'),
              ('\xe5\x8f\xb6\xe8\xa3\x95\xe8\x89\xaf', '2012'),
              ('\xe9\x83\x91\xe6\x96\x87\xe8\xbe\x89', '2007'),
              ('\xe5\x88\x98\xe6\xb0\xb8\xe5\x85\x89', '1997'),
              ('\xe8\x83\xa1\xe7\x87\x95\xe9\xa3\x9e', '2003'),
              ('\xe8\x92\x8b\xe6\xb3\xa2', '2004'),
              ('\xe9\x9f\xa9\xe5\xb0\x8f\xe6\x83\xa0', '2004'),
              ('\xe8\xb4\xba\xe4\xbd\xb3\xe9\xa2\x96', '2004'),
              ('\xe9\x92\x9f\xe4\xbb\xb2\xe5\xbc\xba', '2007'),
              ('\xe5\x88\x98\xe9\x9c\xb2\xe5\xae\x81', '2003'),
              ('\xe8\xa2\x81\xe5\x8d\x83\xe9\x9b\x85', '2007'),
              ('\xe8\xae\xb8\xe7\xba\xaf\xe6\x95\x8f', '2013'),
              ('\xe6\x9b\xbe\xe9\x9b\xaa', '2018'),
              ('\xe6\x9e\x97\xe5\x9f\xb9\xe6\xbc\xa9', '2019'),
              ('\xe4\xb8\x81\xe5\x9d\x9b', '2000'),
              ('\xe9\x9b\xb7\xe8\x89\xb3', '1989'),
              ('\xe6\x9b\xbe\xe6\xb5\xb7', '2003'),
              ('\xe9\x99\x88\xe7\xbe\xa4', '2006'),
              ('\xe9\x99\x88\xe9\x94\xa6\xe7\xab\xa0', '1991'),
              ('\xe5\xbc\xa0\xe5\x8d\xab\xe4\xb8\x9c', '1999'),
              ('\xe8\x8b\x8f\xe5\xb0\x8f\xe5\x86\xac', '2002'),
              ('\xe9\x83\xad\xe6\xb3\x93\xe6\x96\x8c', '2004'),
              ('\xe6\x9d\x8e\xe4\xb8\x9c\xe7\x94\x9f', '2000'),
              ('\xe6\x88\xb4\xe5\x8d\x8e\xe7\x8f\xba', '1993'),
              ('\xe7\xbf\x9f\xe5\x86\xa0\xe6\x99\xb6', '2006'),
              ('\xe5\x88\x98\xe5\xae\x8f', '2007'),
              ('\xe9\xbb\x8e\xe6\x98\xa5\xe9\x9b\xa8', '2007'),
              ('\xe5\xbb\x96\xe5\x9b\xbd\xe9\x91\xab', '2007'),
              ('\xe8\xb5\xb5\xe8\x96\x87', '2013'),
              ('\xe6\x9b\xbe\xe5\x87\xa1\xe5\xbc\xba', '2013'),
              ('\xe9\x99\x88\xe6\x96\xb0\xe5\xae\x87', '2013'),
              ('\xe6\x99\x8b\xe6\x9e\x97', '2005'),
              ('\xe5\x91\xa8\xe6\x9d\xa8', '2009'),
              ('\xe5\xae\x8b\xe5\xba\x86\xe5\xa8\xb4', '2014'),
              ('\xe7\xbd\x97\xe7\x87\x95\xe7\x81\xb5', '1978'),
              ('\xe9\x99\x88\xe6\x99\x93\xe7\xbf\xa0', '2004'),
              ('\xe9\x82\x93\xe6\x85\xa7\xe5\xa9\xb5', '2001'),
              ('\xe5\xbc\xa0\xe5\x8d\x9a', '2017'),
              ('\xe5\xbd\xad\xe5\x86\xac\xe7\xbb\xb4', '2017'),
              ('\xe7\xbd\x97\xe8\xaf\x97\xe7\x90\xb4', '2017'),
              ('\xe8\x94\xa1\xe5\x80\xa9\xe5\x80\xa9', '2017'),
              ('\xe8\xb0\xad\xe7\xbf\xa0\xe8\x8e\xba', '2007'),
              ('\xe5\x85\xb3\xe7\x87\x95\xe5\xa6\xae', '2016'),
              ('\xe7\xbd\x97\xe4\xbd\xb3\xe9\x9f\xb5', '2017'),
              ('\xe6\x9e\x97\xe5\xbe\xb7\xe5\x85\xa8', '2017'),
              ('\xe6\x9d\x8e\xe9\x9d\x99', '2009'),
              ('\xe9\xa1\xbe\xe9\xb9\x8f', '2017'),
              ('\xe9\x99\x88\xe8\x8b\xb1\xe4\xb8\x9c', '2016'),
              ('\xe5\x8f\xb2\xe8\x8e\x89', '2002'),
              ('\xe6\x9e\x97\xe7\x90\xb3', '2006'),
              ('\xe6\x9b\xbe\xe8\x90\x8d', '2007'),
              ('\xe6\x9d\x8e\xe8\x85\xbe', '2017'),
              ('\xe5\x90\xb4\xe7\xa3\x8a', '2015'),
              ('\xe6\x9d\x8e\xe5\xa5\x87', '2016'),
              ('\xe5\xbc\xa0\xe7\xbe\x8e\xe7\x8f\xa0', '2017'),
              ('\xe6\x9d\x8e\xe5\x87\xaf', '2013'),
              ('\xe8\xb0\xa2\xe7\x87\x8a', '2017'),
              ('\xe5\xbc\xa0\xe5\xae\x81\xe5\xa4\x8f', '2018'),
              ('\xe6\x9d\x8e\xe5\xad\x90\xe5\xbd\xac', '2018'),
              ('\xe9\x92\x9f\xe6\x80\x9d\xe6\x95\x8f', '2018'),
              ('\xe6\x96\xb9\xe4\xbe\x9d\xe5\x87\xa1', '2018'),
              ('\xe6\x9d\x8e\xe7\x81\xb5\xe6\x80\xa1', '2018'),
              ('\xe9\xbb\x84\xe6\x98\xa5\xe6\x96\x8c', '2018'),
              ('\xe9\x99\x88\xe8\x8f\x81\xe8\x8f\x81', '2014'),
              ('\xe5\xbe\x90\xe7\x91\x9c', '2017'),
              ('\xe5\x94\x90\xe6\x9b\xbe\xe5\xa8\x81', '2014'),
              ('\xe6\x9d\x8e\xe8\x99\xb9\xe8\x8e\xb9', '2018'),
              ('\xe5\xbb\x96\xe4\xbd\xb3\xe8\x8e\xb9', '2018'),
              ('\xe5\x8c\xba\xe5\x80\xa9\xe7\x90\xb3', '2018'),
              ('\xe7\x8e\x8b\xe6\x98\x95\xe8\x94\x9a', '2014'),
              ('\xe6\x9c\xb1\xe5\xa4\x8f\xe4\xbf\x90', '2017'),
              ('\xe5\xb7\xab\xe6\x99\x93\xe7\x92\x87', '2017'),
              ('\xe6\x9d\x8e\xe6\xbb\xa2', '2018'),
              ('\xe8\xb5\xb5\xe6\x96\x87\xe6\xb0\x91', '1990'),
              ('\xe8\xb5\xb5\xe9\xa3\x9e\xe9\xbe\x99', '2003'),
              ('\xe5\x8f\xb6\xe6\x98\xad\xe9\xbe\x99', '2004'),
              ('\xe5\x88\x98\xe7\x91\xbe\xe7\x86\xa0', '2015'),
              ('\xe5\xbc\xa0\xe5\xae\xb6\xe8\xaa\x89', '2017'),
              ('\xe5\xbc\xa0\xe8\xbe\xbe\xe6\x99\xae', '2017'),
              ('\xe5\xbc\xa0\xe6\x88\x90\xe5\x88\x9a', '1998'),
              ('\xe8\x8b\x8f\xe4\xba\x91\xe6\x8d\xb7', '2015'),
              ('\xe6\x9d\x8e\xe5\xa9\xa7', '2019'),
              ('\xe5\x8f\xb6\xe5\xad\x90\xe8\xb1\xaa', '2018'),
              ('\xe9\xbb\x84\xe6\x99\x93\xe6\xbb\xa8', '1995'),
              ('\xe8\xb5\xb5\xe4\xbf\x8a\xe6\x98\x8c', '2001'),
              ('\xe4\xbb\x9d\xe9\x94\x90', '1998'),
              ('\xe5\xbc\xa0\xe5\x9b\xbd\xe8\x89\xaf', '2006'),
              ('\xe8\xae\xb8\xe6\x99\xb4\xe4\xb8\xbd', '2018'),
              ('\xe5\xbd\xad\xe7\xab\xa0\xe5\xb9\xb3', '2007'),
              ('\xe9\x82\x93\xe5\x98\x89\xe5\x85\xb4', '2007'),
              ('\xe9\x99\x88\xe5\xb0\x8f\xe5\x86\xac', '2001'),
              ('\xe9\x99\x86\xe7\x9d\xbf', '2003'),
              ('\xe9\xbe\x9a\xe4\xb8\xbd\xe5\x8d\xbf', '2007'),
              ('\xe4\xbe\xaf\xe6\xac\xa2\xe6\xac\xa2', '2008'),
              ('\xe5\x90\xb4\xe4\xb8\xb9', '2013'),
              ('\xe5\x90\xb4\xe5\x8d\x87\xe9\x9b\x81', '2017'),
              ('\xe6\x9b\xbe\xe5\xae\x87', '1990'),
              ('\xe6\xb1\x9f\xe5\x8d\x97', '1988'),
              ('\xe5\xbc\xa0\xe6\xb4\x81\xe4\xb8\xbd', '1996'),
              ('\xe5\xbc\xa0\xe7\x88\xb1\xe4\xb8\xbd', '1997'),
              ('\xe9\x83\x91\xe9\x9f\xa6\xe4\xbc\x9f', '2004'),
              ('\xe5\xbb\x96\xe9\x9b\xaf\xe9\x9d\x99', '2010'),
              ('\xe8\xb5\xb5\xe8\xb6\x8a', '2006'),
              ('\xe5\xbc\xa0\xe4\xb8\xbd\xe8\x90\x8d', '1999'),
              ('\xe7\x8e\x8b\xe8\x81\xaa', '2003'),
              ('\xe6\x9b\xbe\xe6\xad\xa3\xe4\xb8\xad', '2001'),
              ('\xe8\xa9\xb9\xe5\xbd\xa6', '2008'),
              ('\xe5\xae\x98\xe4\xb9\x90\xe6\x80\xa1', '2016'),
              ('\xe6\x9d\x8e\xe5\xb9\xbf\xe4\xb8\x9a', '2013'),
              ('\xe7\xbd\x97\xe4\xb8\x81\xe8\x81\xaa', '2015'),
              ('\xe5\xbc\xa0\xe6\x94\xbf', '2018'),
              ('\xe8\xb5\x96\xe6\xb0\xb8\xe7\x81\xb5', '2008'),
              ('\xe5\x90\xb4\xe6\xb5\xb7\xe5\xbc\xba', '2004'),
              ('\xe6\x9b\xbe\xe5\xba\x86\xe5\xbf\xa0', '2017'),
              ('\xe5\x88\x98\xe5\xbf\x97\xe5\xb3\xb0', '1991'),
              ('\xe9\x83\xad\xe6\x99\xa8', '2001'),
              ('\xe5\xbc\xa0\xe5\xbf\x97\xe9\xbe\x99', '2008'),
              ('\xe6\x9d\x8e\xe5\xb3\xb0', '2003'),
              ('\xe6\x9b\xbe\xe7\x9b\x9b\xe9\xa3\x9e', '2004'),
              ('\xe5\xb7\xab\xe6\x97\xad\xe6\x98\xa5', '1995'),
              ('\xe7\xbd\x97\xe8\x89\xb3', '2009'),
              ('\xe9\x92\x9f\xe4\xb8\xbd\xe5\xa8\x9c', '2014'),
              ('\xe7\xbd\x97\xe4\xbf\x8a\xe5\xbb\xba', '2017'),
              ('\xe5\xae\x8b\xe6\xa2\x93\xe5\xba\xb7', '2017'),
              ('\xe8\x96\x9b\xe6\xb3\xbd\xe7\x80\x9a', '2017'),
              ('\xe7\xbd\x97\xe8\x8f\x8a\xe6\xa0\xb9', '1997'),
              ('\xe6\x9d\x8e\xe4\xbd\xb3\xe7\x8f\x8d', '2018'),
              ('\xe9\x83\xad\xe6\x96\x87\xe6\x8d\xb7', '1993'),
              ('\xe8\xae\xb8\xe5\xb7\xa7\xe7\x87\x95', '2001'),
              ('\xe5\x86\xaf\xe8\x8a\xb1', '2011'),
              ('\xe9\x9f\xa9\xe7\xa7\x8b\xe5\xb9\xb3', '1998'),
              ('\xe6\x9b\xbe\xe5\xbb\xba\xe8\x8b\xb1', '2003'),
              ('\xe5\xbe\x90\xe8\xbf\x8e\xe4\xb8\xbd', '2007'),
              ('\xe9\x99\x88\xe6\xb5\xb7\xe6\xbb\xa8', '1997'),
              ('\xe5\x87\x8c\xe8\x89\xba\xe6\xa1\x90', '1999'),
              ('\xe5\x8d\xa2\xe6\x85\xa7\xe7\x90\xb3', '2003'),
              ('\xe9\x9f\xa9\xe6\xbb\x94', '1995'),
              ('\xe5\x8f\xb2\xe4\xb8\x80\xe6\xb6\xb5', '2005'),
              ('\xe5\x8d\x93\xe7\x92\x90\xe7\x92\x90', '2003'),
              ('\xe8\x8c\x83\xe5\x85\xa8', '2014'),
              ('\xe9\xbb\x84\xe4\xb8\xbd\xe5\x90\x9b', '2013'),
              ('\xe5\x88\x98\xe8\x90\x8d\xe9\xab\x98\xe9\x9b\x81', '2016'),
              ('\xe5\x94\x90\xe5\x98\x89\xe9\xaa\x8f', '2017'),
              ('\xe5\x88\x98\xe8\x8c\xb9\xe9\x91\xab', '2017'),
              ('\xe5\x91\xa8\xe4\xb9\xa6\xe8\x81\xaa', '2017'),
              ('\xe8\x94\xa1\xe5\xae\x87', '2017'),
              ('\xe8\xb5\x96\xe4\xbc\x9f\xe9\xb9\x8f', '2018'),
              ('\xe6\x9e\x97\xe4\xbc\x9f\xe9\xb9\x8f', '2016'),
              ('\xe6\x9d\x8e\xe5\x98\x89', '2016'),
              ('\xe8\x8b\x8f\xe9\x9c\x9e', '2017'),
              ('\xe6\x9b\xb9\xe6\xb1\x89\xe6\x98\x8e', '2006'),
              ('\xe6\x9d\x8e\xe5\xbf\xa0\xe6\x95\x8f', '1997')]
        accounts = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_SAMPLE)
        umap = {}
        for a in accounts:
            umap[a['name']] = a
        cur = 2019
        success = 0
        for user in us:
            if not umap.has_key(user[0]):
                self.elog('annual %s' % user[0])
                continue
            # uid = umap[user[0]]['id']
            # success += 1
            # df = cur - int(user[1])
            # if df >= 20:
            #     total = 15
            # elif df >= 10:
            #     total = 10
            # else:
            #     total = 5
            # annual = {
            #     'uid': uid,
            #     'total': total,
            #     'begin_year': int(user[1]),
            # }
            # yield self.job_dao.add_annual_leave(**annual)
        self.wlog('annual %s' % success)



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
