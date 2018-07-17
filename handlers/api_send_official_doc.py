# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define
from api_handler import ApiHandler
from job_timer import JobTimer

class ApiSendOfficialDoc(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        time = self.now()
        op = self.get_argument_and_check_it('op')
        job_type = self.get_argument('type', type_define.TYPE_JOB_OFFICIAL_DOC)
        if op == 'add':
            job_record = {
                'type': job_type,
                'invoker': self.account_info['id'],
                'time': time,
                'mod_time': time,
                'status': type_define.STATUS_JOB_PROCESSING,
                'sub_type': int(self.get_argument('sub_type', type_define.TYPE_JOB_OFFICIAL_DOC_GROUP)),
            }
            fields = ['title']
            for field in fields:
                job_record[field] = self.get_argument_and_check_it(field)
            job_id = yield self.job_dao.create_new_job(**job_record)
            self.check_result_and_finish_while_failed(job_id, '创建工作流失败')
        elif op == 'reply':
            job_id = self.get_argument_and_check_it('job_id')
            job_record = yield self.job_dao.query_job_base_info(job_id)
            self.check_result_and_finish_while_failed(job_record, '工作流不存在')
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '参数错误')
            return


        job_node = {
            'job_id': job_id,
            'time': time,
            'sender_id': self.account_info['id'],
        }
        fields = ['content', 'has_attachment', 'has_img']
        for field in fields:
            job_node[field] = self.get_argument_and_check_it(field)
        node_type = self.get_argument('node_type', None)
        if node_type:
            job_node['type'] = node_type
        rec_id = self.get_argument('rec_id', None)
        set_id = None
        rec_set = None
        if rec_id is not None:
            job_node['rec_id'] = rec_id
        else:
            rec_set = self.get_argument('rec_set', None)
            if rec_set is None:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '接收者参数不合法')
            rec_set = set(self.loads_json(rec_set))
            rec_set -= set([job_record['invoker']])
            if op == 'add':
                set_id = yield self.job_dao.create_uid_set()
                if not set_id:
                    self.finish_with_error(error_codes.EC_SYS_ERROR, '创建uid set失败')
            if job_record['sub_type'] == type_define.TYPE_JOB_SUB_TYPE_GROUP:
                if len(rec_set) > 0:
                    extend = '{*【以下成员加入工作流】*}\n'
                    rec_accounts = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_SAMPLE, uid_list=list(rec_set))
                    for account in rec_accounts:
                        extend += '　　%s　　%s　　%s\n' % (account['account'], account['name'], account['dept'])
                    job_node['extend'] = '{%s}' % extend
                if not set_id:
                    first_node = yield self.job_dao.query_first_job_node(job_id)
                    set_id = first_node['rec_set']
                    if not set_id:
                        self.finish_with_error(error_codes.EC_SYS_ERROR, '系统错误：rec_set不合法')
            job_node['rec_set'] = set_id
        branch_id = self.get_argument('branch_id', None)
        if branch_id:
            job_node['branch_id'] = branch_id
        node_id = yield self.job_dao.add_job_node(**job_node)
        if not node_id:
            if op == 'add':
                yield self.job_dao.delete_job(job_id)
            self.finish_with_error(error_codes.EC_SYS_ERROR, '创建工作流节点失败')

        # if op == 'reply':
        #     yield self.job_dao.update_job_mark(job_id, self.account_info['id'], type_define.STATUS_JOB_MARK_PROCESSED,branch_id)

        attachment_fields = [
            ['has_attachment', 'file_list', type_define.TYPE_JOB_ATTACHMENT_NORMAL],
            ['has_img', 'img_list', type_define.TYPE_JOB_ATTACHMENT_IMG],
        ]
        for field in attachment_fields:
            if job_node[field[0]] == '1':
                file_list = self.get_argument_and_check_it(field[1])
                file_list = self.loads_json(file_list)
                job_attachment = {'node_id': node_id}
                for path_id in file_list:
                    path_info = yield self.job_dao.query_file_path(path_id)
                    job_attachment['name'] = path_info['filename']
                    job_attachment['path'] = path_info['path']
                    job_attachment['type'] = field[2]
                    yield self.job_dao.add_node_attachment(**job_attachment)

        self.process_result(True, '发送公文')
        if set_id:
            yield self.job_dao.insert_into_uid_set(set_id, rec_set)
            rec_set = yield self.job_dao.query_uid_set(set_id)
            rec_set = set([item['uid'] for item in rec_set])
            rec_set.add(job_record['invoker'])
            rec_set.remove(self.account_info['id'])
            if job_record['sub_type'] == type_define.TYPE_JOB_SUB_TYPE_BRANCH:
                for uid in rec_set:
                    yield self.job_dao.update_job_mark(job_id, uid, type_define.STATUS_JOB_MARK_WAITING, uid)
            else:
                push_alias = []
                for uid in rec_set:
                    yield self.job_dao.update_job_mark(job_id, uid, type_define.STATUS_JOB_MARK_WAITING)
                    push_alias.append('%s' % uid)
                self.debug_info({"alias" : push_alias})
                content = job_node['content'][1:-1]
                length = len(content)
                if length == 0:
                    content = u'【无内容】'
                else:
                    content = u'【新消息】%s' % self.get_content_part(content, 0, 15)
                extra = {
                    "type": job_record['type'],
                    "job_id": job_id,
                    'title': job_record['title'],
                    'content': content,
                    'sender': self.account_info['name']
                }
                self.push_server.push_with_alias("", push_alias, extra)
                return
        else:
            yield self.job_dao.update_job_mark(job_id, rec_id, type_define.STATUS_JOB_MARK_WAITING, branch_id)
            yield self.job_dao.update_job_mark(job_id, self.account_info['id'], type_define.STATUS_JOB_MARK_PROCESSED, branch_id)




