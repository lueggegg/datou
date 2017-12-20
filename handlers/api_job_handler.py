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

    def is_type_of_leave(self, job_type):
        return job_type in [type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY,
                        type_define.TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY,
                        type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY,
                        type_define.TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY,
                        type_define.TYPE_JOB_LEAVE_FOR_BORN_NORMAL,
                        type_define.TYPE_JOB_LEAVE_FOR_BORN_LEADER, ]

