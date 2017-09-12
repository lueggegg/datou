# -*- coding: utf-8 -*-

import type_define
import error_codes

from api_handler import ApiHandler

from tornado import gen

class ApiCommonConfig(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}

        op = self.get_argument_and_check_it('op')
        config_type = self.get_argument_and_check_it('config_type')

        ret = True
        msg = ''
        if op == 'query':
            ret = yield self.config_dao.query_common_config(config_type)
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'update':
            config_data = self.get_argument_and_check_it('config_data')
            config_data = self.loads_json(config_data)
            for config in config_data:
                self.config_dao.set_common_config(config_type, config['key'], config['label'])
        else:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '参数op错误')

        self.process_result(ret, msg)