# -*- coding: utf-8 -*-

from tornado import gen
from tornado.template import Loader
import os
import re
import codecs
import zipfile

import error_codes
import type_define

from api_job_handler import JobHandler


class ApiJobExport(JobHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument_and_check_it('op')

        if op == 'single':
            job_id = self.get_argument_and_check_it('job_id')
            file_path = yield self.generate_export_file(job_id)
            zip_path = [item + '.zip' for item in file_path]
            if not os.path.isfile(zip_path[1]):
                handle = zipfile.ZipFile(zip_path[1],'w',zipfile.ZIP_DEFLATED)
                handle.write(file_path[1], file_path[2])
                handle.close()
            self.write_data(zip_path[0])
        elif op == 'chunk':
            job_list = self.get_argument_and_check_it('job_list')
            job_list = self.loads_json(job_list)
            filename = 'job_list_%s.zip' % self.get_current_hash()
            zip_file = self.get_res_file_path(filename, 'res/temp', True)
            net_file = self.get_res_file_path(filename, 'res/temp')
            handle = zipfile.ZipFile(zip_file,'w',zipfile.ZIP_DEFLATED)
            for job_id in job_list:
                file_path = yield self.generate_export_file(job_id)
                handle.write(file_path[1], file_path[2])
            handle.close()
            self.write_data(net_file)
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')

    @gen.coroutine
    def generate_export_file(self, job_id):
        main_info = yield self.job_dao.query_job_base_info(job_id)
        if main_info['status'] not in [type_define.STATUS_JOB_REJECTED, type_define.STATUS_JOB_COMPLETED]:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '%s未归档')
        filename = 'job_%s_%s.html' % (job_id, main_info['title'].decode('utf-8'))
        dir_path = 'res/download/job_export'
        net_path = self.get_res_file_path(filename, dir_path)
        file_path = self.get_res_file_path(filename, dir_path, True)
        if os.path.isfile(file_path):
            raise gen.Return([net_path, file_path, filename])
        status_map = {
            type_define.STATUS_JOB_PROCESSING: '处理中',
            type_define.STATUS_JOB_COMPLETED: '已完成',
            type_define.STATUS_JOB_CANCEL: '已撤回',
            type_define.STATUS_JOB_REJECTED: '未通过',
        }
        main_info['status'] = status_map[main_info['status']]
        branch_id = self.get_argument('branch_id', None)
        node_list = yield self.job_dao.query_job_node_list(job_id, branch_id)
        for item in node_list:
            attachment_type = [
                ['has_attachment', type_define.TYPE_JOB_ATTACHMENT_NORMAL, 'attachment'],
                ['has_img', type_define.TYPE_JOB_ATTACHMENT_IMG, 'img_attachment'],
            ]
            for _type in attachment_type:
                if item[_type[0]]:
                    attachment = yield self.job_dao.query_node_attachment_list(item['id'], _type[1])
                    item[_type[2]] = attachment
            content = self.abstract_job_content(item['content'])
            content = self.html_to_text(content)
            item['content'] = content
        if node_list[0]['rec_set']:
            rec_set = yield self.job_dao.query_uid_set(node_list[0]['rec_set'])
        else:
            rec_set = None
        loader = Loader(self.get_template_path(), autoescape=None)
        result = loader.load('base_job_export.html').generate(
            rec_set=rec_set,
            main_info=main_info,
            node_list=node_list,)
        fid = codecs.open(file_path, 'w', encoding='utf-8')
        fid.write(result.decode('utf-8'))
        raise gen.Return([net_path, file_path, filename])

    def abstract_job_content(self, content):
        return content[1:-1]

    def html_to_text(self, string):
        p = re.compile(r'([ <>&"\n\r])')
        string = p.sub(self.html_to_text_map, string)
        p = re.compile(r'\{\*(.*?)\*\}')
        string = p.sub(r'<span>\1</span>', string)
        return string

    def html_to_text_map(self, m):
        the_map = {
            ' ': '&nbsp;',
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            '\n': "<br/>",
            '\r': "<br/>",
        }
        o = m.group(1)
        return the_map[o] if o in the_map else o
