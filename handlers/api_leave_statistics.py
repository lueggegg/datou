# -*- coding: utf-8 -*-

from tornado import gen
from api_handler import ApiHandler
import datetime

class ApiLeaveStatistics(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        fields = ['dept_id', 'leave_type', 'min_begin_time', 'max_begin_time']
        kwargs = {}
        self.travel_argument(kwargs, fields)
        ret = yield self.job_dao.query_leave_detail_list(**kwargs)
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
        path = self.generate_excel_file(data, 'leave_statistics')
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



