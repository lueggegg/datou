# -*- coding: utf-8 -*-

import type_define
import error_codes

from api_handler import ApiHandler

from tornado import gen

class ApiOuterLinkHandler(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        res = {'status': error_codes.EC_SUCCESS}

        op = self.get_argument_and_check_it('op')
        link_type = self.get_argument('type', None)

        ret = True
        msg = ''
        if op == 'query':
            if not link_type:
                self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '缺少参数type')
            count = self.get_argument('count', None)
            offset = self.get_argument('offset', 0)
            ret = yield self.config_dao.query_outer_link(link_type=link_type, count=count, offset=offset)
            res['data'] = ret
            yield self.write_json(res)
            return
        elif op == 'add' or op == 'update':
            info = {}
            info['url'] = self.get_argument_and_check_it('url')
            info['title'] = self.get_argument_and_check_it('title')
            if 'img_url' in self.request.arguments:
                info['img_url'] = self.get_argument_and_check_it('img_url')
            if op == 'add':
                info['type'] = self.get_argument_and_check_it('type')
                msg = '添加链接'
                ret = yield self.config_dao.add_outer_link(**info)
            else:
                msg = '更新链接'
                link_id = self.get_argument_and_check_it('link_id')
                ret = yield self.config_dao.update_outer_link(link_id, **info)
        elif op == 'top':
            msg = '置顶链接'
            link_id = self.get_argument_and_check_it('link_id')
            ret = yield self.config_dao.update_outer_link(link_id, mod_time=self.now())
        elif op == 'del':
            msg = '删除链接'
            link_id = self.get_argument_and_check_it('link_id')
            ret = yield self.config_dao.del_outer_link(link_id)
        else:
            self.finish_with_error(error_codes.EC_SYS_ERROR, '参数op错误')

        self.process_result(ret, msg)