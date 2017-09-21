# -*- coding: utf-8 -*-

import type_define
import error_codes

from api_handler import ApiHandler

from tornado import gen

class ApiRuleType(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}

        op = self.get_argument_and_check_it('op')

        ret = True
        msg = ''
        if op == 'query':
            ret = yield self.config_dao.query_rule_type_list()
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'add' or op == 'update':
            info = {}
            if op == 'add':
                msg = '添加制度类型'
                info['label'] = self.get_argument_and_check_it('label')
                ret = yield self.config_dao.add_rule_type(**info)
            else:
                msg = '更新制度类型'
                type_id = self.get_argument_and_check_it('type_id')
                self.travel_argument(info, ['label', 'memo'])
                if info:
                    ret = yield self.config_dao.update_rule_type(type_id, **info)
        elif op == 'del':
            msg = '删除制度类型'
            type_id = self.get_argument_and_check_it('type_id')
            ret = yield self.config_dao.del_rule_type(type_id)
        else:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '参数op错误')

        self.process_result(ret, msg)