# -*- coding: utf-8 -*-

from tornado import gen
from api_handler import ApiHandler
import datetime

class ApiLeaveStatistics(ApiHandler):

    @gen.coroutine
    def process_leave_sum(self):
        fields = ['dept_id', 'min_begin_time', 'max_begin_time']
        kwargs = {}
        self.travel_argument(kwargs, fields)
        leave_types = ['事假', '病假', '婚假', '丧假', '产假', '陪产假', '因公', '其他']
        title = ['序号', '部门', '姓名', '应休年假', '已休年假', '剩余年假']
        title.extend(leave_types)
        data = [title]
        annual_list = yield self.job_dao.query_annual_leave_list()
        annual_map = {}
        for index, annual in enumerate(annual_list):
            annual_map[annual['uid']] = annual
            row = [index+1, annual['dept'], annual['name'], annual['total'], annual['used'], annual['total']-annual['used']]
            for key in leave_types:
                row.append(0)
            data.append(row)
        path = self.generate_excel_file(data, 'leave_sum_statistics')
        self.write_data(path)


    @gen.coroutine
    def _real_deal_request(self):
        if self.get_argument('sum', None):
            yield self.process_leave_sum()
            return

        fields = ['dept_id', 'leave_type', 'min_begin_time', 'max_begin_time']
        kwargs = {}
        self.travel_argument(kwargs, fields)
        ret = yield self.job_dao.query_new_leave_detail_list(**kwargs)
        if not ret:
            self.finish_with_error(3, '没有数据')
        title = ['序号', '部门', '姓名', '请假类型', '请假日期', '天数（工作日）', '备注']
        data = [title]
        index = 0
        for item in ret:
            index += 1
            line = [
                str(index),
                item['dept'],
                item['name'],
                item['leave_type'],
                '%s ～ %s' % (item['begin_time'], item['end_time']),
            ]
            if item['half_day'] is None:
                line.append(self.get_workdays(item['begin_time'], item['end_time']))
            else:
                line.append('%.1f天' % (0.5*item['half_day'], ))
            data.append(line)
        path = self.generate_excel_file(data, 'leave_detail_statistics')
        self.write_data(path)


    def get_workdays(self, begin_time, end_time, on=datetime.time(hour=9), off=datetime.time(hour=18)):
        if end_time < begin_time:
            self.finish_with_error(3, '结束时间小于开始时间')
        begin_date = begin_time.date()
        end_date = end_time.date()
        days = (end_date - begin_date).days
        weekday = begin_time.weekday()
        days += weekday
        workdays = (days/7)*5 + days%7 - weekday
        time_begin = begin_time.time()
        time_end = end_time.time()
        valid_begin = on
        valid_end = off
        work_interval = off.hour - on.hour
        if weekday not in (5, 6):
            if time_begin >= off:
                workdays -= 1
            elif time_begin >= on:
                valid_begin = time_begin
        weekday = end_time.weekday()
        if weekday not in (5, 6):
            if time_end <= on:
                workdays -= 1
            elif time_end <= off:
                valid_end = time_end
        else:
            workdays -= 1
        hours = 0
        if valid_end > valid_begin:
            hours = valid_end.hour - valid_begin.hour
        elif valid_end < valid_begin:
            hours += work_interval - (valid_begin.hour - valid_end.hour)
            workdays -= 1
        if hours == work_interval:
            workdays += 1
            hours = 0
        if workdays == 0:
            return '%s小时' % hours
        if hours == 0:
            return '%s天' % workdays
        return '%s天 %s小时' % (workdays, hours)



