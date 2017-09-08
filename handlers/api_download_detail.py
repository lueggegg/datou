# -*- coding: utf-8 -*-

import type_define
import error_codes

from api_handler import ApiHandler

from tornado import gen

class ApiDownloadDetail(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}

        op = self.get_argument_and_check_it('op')

        ret = True
        msg = ''
        if op == 'query':
            type_id = self.get_argument('type_id', None)
            ret = yield self.config_dao.query_download_detail_list(type_id)
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'del':
            msg = '删除文件'
            file_id = self.get_argument_and_check_it('file_id')
            ret = yield self.config_dao.del_download_detail(file_id)
        else:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '参数op错误')

        self.process_result(ret, msg)