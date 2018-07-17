# -*- coding: utf-8 -*-

from tornado import gen
from base_handler import BaseHandler
import error_codes
import config
import codecs

class ApiHandler(BaseHandler):
    __dept_map = None
    __dept_tree = None

    def get_tag(self):
        return 'api'

    def get(self, *args, **kwargs):
        if config.allow_api_by_get:
            return self.post(*args, **kwargs)
        self.send_error(404)

    def process_result(self, ret, msg):
        if not ret:
            self.finish_with_error(error_codes.EC_SYS_ERROR, msg + '失败')
        else:
            self.write_result(error_codes.EC_SUCCESS, msg + '成功')
        self.finish()

    @gen.coroutine
    def on_dept_info_changed(self):
        dept_list = yield self.account_dao.query_dept_list()

        dept_map = {}
        for item in dept_list:
            dept_map[item['id']] = item
        ApiHandler.__dept_map = dept_map

        dept_tree = {0: [None]}
        for dept in dept_list:
            if dept['id'] not in dept_tree:
                dept_tree[dept['id']] = [dept]
            else:
                dept_tree[dept['id']].insert(0, dept)

            if dept['parent']:
                if dept['parent'] not in dept_tree:
                    dept_tree[dept['parent']] = [dept]
                else:
                    dept_tree[dept['parent']].append(dept)
            else:
                dept_tree[0].append(dept)
        self.assign_department_level(dept_tree)
        ApiHandler.__dept_tree = dept_tree

    @gen.coroutine
    def get_department_map(self):
        if ApiHandler.__dept_map is None:
            yield self.on_dept_info_changed()
        raise gen.Return(ApiHandler.__dept_map)

    @gen.coroutine
    def get_department_tree(self, with_level=False):
        if ApiHandler.__dept_tree is None:
            yield self.on_dept_info_changed()
        raise gen.Return(ApiHandler.__dept_tree)

    def assign_department_level(self, dept_tree):
        for top_dept in dept_tree[0][1:]:
            self.travel_assign_department_level(dept_tree, top_dept['id'], 0)

    def travel_assign_department_level(self, dept_tree, dept_id, level):
        dept_tree[dept_id][0]['level'] = level
        for child in dept_tree[dept_id][1:]:
            self.travel_assign_department_level(dept_tree, child['id'], level+1)

    def travel_argument(self, info, fields):
        for field in fields:
            arg = self.get_argument(field, None)
            if arg is not None:
                info[field] = arg

    def generate_excel_file(self, data, filename_prefix='statistics', target_dir='res/temp'):
        filename = filename_prefix + '_' + self.get_current_hash() + '.csv'
        file_path = self.get_res_file_path(filename, target_dir, True)
        # fid = codecs.open(file_path, 'w', 'utf-8')
        fid = open(file_path, 'w')
        string = ''
        for line in data:
            if not line:
                string += '\n'
                continue
            line = ['%s' % item for item in line]
            string += ','.join(line) + '\n'
        fid.write(string)
        fid.close()
        return '/%s/%s' % (target_dir, filename)

    def abstract_account(self, account, fields):
        obj = {}
        for field in fields:
            obj[field] = account[field]
        return obj

    def get_content_part(self, content, begin, count, end=0):
        if begin != 0 or end != 0:
            content = content[begin:end]
        size = len(content)
        return content if size <= count else content[0:count] + '...'


class ApiNoVerifyHandler(ApiHandler):
    def post(self, *args, **kwargs):
        return self._deal_request(False)