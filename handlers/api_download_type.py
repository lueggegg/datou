# -*- coding: utf-8 -*-

import type_define
import error_codes

from api_handler import ApiHandler

from tornado import gen

class ApiDownloadType(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}

        op = self.get_argument_and_check_it('op')

        ret = True
        msg = ''
        if op == 'query':
            parent_type = self.get_argument('type', None)
            ret = yield self.config_dao.query_download_type_list(parent_type)
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'add' or op == 'update':
            info = {}
            info['label'] = self.get_argument_and_check_it('label')
            if op == 'add':
                info['type'] = self.get_argument_and_check_it('type')
                msg = '添加文件类型'
                ret = yield self.config_dao.add_download_type(**info)
            else:
                msg = '更新文件类型'
                type_id = self.get_argument_and_check_it('type_id')
                ret = yield self.config_dao.update_download_type(type_id, **info)
        elif op == 'del':
            msg = '删除文件类型'
            type_id = self.get_argument_and_check_it('type_id')
            ret = yield self.config_dao.del_download_type(type_id)
        else:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '参数op错误')

        self.process_result(ret, msg)