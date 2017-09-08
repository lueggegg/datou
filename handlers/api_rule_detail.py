# -*- coding: utf-8 -*-

import type_define
import error_codes

from api_handler import ApiHandler

from tornado import gen

class ApiRuleDetail(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}

        op = self.get_argument_and_check_it('op')

        ret = True
        msg = ''
        if op == 'query':
            type_id = self.get_argument('type_id', None)
            ret = yield self.config_dao.query_rule_detail_list(type_id)
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'add':
            msg = '添加制度条目'
            info = self.get_argument_and_check_it('rule_info')
            info = self.loads_json(info)
            ret = yield self.config_dao.add_rule_detail(**info)
        elif op == 'del':
            msg = '删除制度条目'
            rule_id = self.get_argument_and_check_it('rule_id')
            ret = yield self.config_dao.del_rule_detail(rule_id)
        elif op == 'update':
            msg = '更新制度条目'
            rule_id = self.get_argument_and_check_it('rule_id')
            info = self.get_argument_and_check_it('rule_info')
            info = self.loads_json(info)
            ret = yield self.config_dao.update_rule_detail(rule_id, **info)
        else:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '参数op错误')

        self.process_result(ret, msg)