# -*- coding: utf-8 -*-
import re
import base64
import hashlib
import os
import type_define

from tornado import gen

import error_codes
from api_handler import ApiHandler

class ApiUploadFile(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        file_type = int(self.get_argument('type', type_define.TYPE_JOB_ATTACHMENT_NORMAL))
        filename = self.get_argument_and_check_it('name')
        file_data = self.get_argument_and_check_it('file_data')
        need_md5_dir = True
        if file_type == type_define.TYPE_JOB_ATTACHMENT_IMG:
            r = re.match('data:image/(.+);base64,(.+)', file_data)
            parent_dir = 'res/attachment/images'
        elif file_type == type_define.TYPE_JOB_ATTACHMENT_NORMAL:
            r = re.match('data:(.*);base64,(.+)', file_data)
            parent_dir = 'res/attachment'
        elif file_type in [type_define.TYPE_UPLOAD_FILE_TO_DOWNLOAD, type_define.TYPE_UPLOAD_RULE_FILE]:
            r = re.match('data:(.*);base64,(.+)', file_data)
            parent_dir = 'res/download'
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, 'file_type错误')

        if not r:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '文件数据格式错误')

        postfix = r.group(1)
        base64_data = r.group(2)
        md5 = hashlib.md5()
        md5.update(base64_data)
        data_md5 = md5.hexdigest()

        if file_type == type_define.TYPE_JOB_ATTACHMENT_IMG:
            net_filename = data_md5 + '.' + postfix
            file_path = self.get_res_file_path(net_filename, parent_dir, True)
            net_path = os.path.join(parent_dir, net_filename)
        else:
            dir_path = self.get_res_file_path(data_md5, parent_dir, True)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            file_path = '%s/%s' % (dir_path, filename)
            net_path = os.path.join('%s/%s' % (parent_dir, data_md5), filename)

        if not os.path.isfile(file_path):
            fid = open(file_path, 'wb')
            fid.write(base64.decodestring(base64_data))
            fid.close()

        if file_type == type_define.TYPE_UPLOAD_FILE_TO_DOWNLOAD:
            type_id = self.get_argument_and_check_it('type_id')
            path_id = yield self.config_dao.add_download_detail(title=filename, path=net_path, type_id=type_id)
        elif file_type == type_define.TYPE_UPLOAD_RULE_FILE:
            path_id = 'useless'
        else:
            path_id = yield self.job_dao.add_file_path(filename=filename, path=net_path)
        if not path_id:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '写入文件路径失败')
        res = {
            'status': error_codes.EC_SUCCESS,
            'path_id': path_id,
            'path': net_path,
            'type': file_type,
            'data': {'path': net_path},
        }
        self.write_json(res)
