# -*- coding: utf-8 -*-
from tornado import gen

import error_codes
from api_handler import ApiNoVerifyHandler

class YcUpload(ApiNoVerifyHandler):

    @gen.coroutine
    def _real_deal_request(self):
        if self.get_argument('op', '') == 'query':
            ret = yield self.job_dao.yc_query_upload()
            self.write_data(ret)
            return
        file_path = self.get_argument_and_check_it("path")
        yield self.job_dao.yc_new_upload(file_path)
        return