# -*- coding: utf-8 -*-

from base_handler import BaseHandler, HttpClient
from tornado import gen
from datetime import datetime

class DetailWorkOffHandler(BaseHandler):

    def get_time_desc(self, time_obj):
        day_part = {
            0: '上午',
            1: '下午'
        }
        time = time_obj['time']
        return '%d年%d月%d日%s' % (time.year, time.month, time.day, day_part[time['part']])

    @gen.coroutine
    def get(self, *args, **kwargs):
        begin = {
            'time': datetime(2019, 6, 1),
            'part': 0
        }
        end = {
            'time': datetime(2019, 6, 5),
            'part': 1
        }
        total = 4.5
        detail = {
            'applicant': 'dwg',
            'department': '大伟部',
            'type': '事假',
            'total_annual': 10,
            'used_annual': 2,
            'pre_judgement': '',
            'reason': '无事生非',
            'time': '自%s至%s，假期内工作日共%s天' % (self.get_time_desc(begin), self.get_time_desc(end), total),
            'department_leader_judgement': '',
            'via_leader_judgement': '',
            'hr_leader_judgement': '',
            'main_leader_judgement': '',
            'hr_department_record': '',
            'attachment': [{
                'path': 'https://baidu.com',
                'name': '百度',
            }, {
                'path': 'https://nba.hupu.com',
                'name': '虎扑',
            }]
        }
        self.render('detail_work_off.html', account_info=self.account_info, detail=detail)

    @gen.coroutine
    def post(self, *args, **kwargs):
        pass
