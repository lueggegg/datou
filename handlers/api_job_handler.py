# -*- coding: utf-8 -*-

import type_define
import error_codes
from tornado import gen

from api_handler import ApiHandler

class JobHandler(ApiHandler):

    def check_job_type(self, job_type):
        valid = job_type > type_define.TYPE_JOB_BEGIN and job_type < type_define.TYPE_JOB_END
        if not valid:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '工作流类型错误')

