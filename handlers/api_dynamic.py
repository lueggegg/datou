# -*- coding: utf-8 -*-

from tornado import gen

import error_codes
import type_define
from api_handler import ApiHandler

class ApiDynamic(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        time = self.now()
        op = self.get_argument_and_check_it('op')
        job_type = self.get_argument('type', type_define.TYPE_JOB_DYNAMIC)
        system = yield self.account_dao.query_pure_account('system')
        if op == 'add':
            job_record = {
                'type': job_type,
                'invoker': system['id'],
                'last_operator': self.account_info['id'],
                'time': time,
                'mod_time': time,
                'status': type_define.STATUS_JOB_COMPLETED,
            }
            fields = ['title']
            for field in fields:
                job_record[field] = self.get_argument_and_check_it(field)
            job_id = yield self.job_dao.create_new_job(with_mark=False, **job_record)
            self.check_result_and_finish_while_failed(job_id, '创建工作流失败')
        elif op == 'del':
            job_id = self.get_argument_and_check_it('job_id')
            ret = yield self.job_dao.update_job(job_id, status=type_define.STATUS_JOB_INVALID)
            self.process_result(ret, '删除动态')
            return
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
        node_id = yield self.job_dao.add_job_node(**job_node)
        if not node_id:
            if op == 'add':
                yield self.job_dao.delete_job(job_id)
            self.finish_with_error(error_codes.EC_SYS_ERROR, '创建工作流节点失败')

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

        self.process_result(True, '发布动态')




