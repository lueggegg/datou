# -*- coding: utf-8 -*-

from tornado import gen

from api_handler import ApiHandler
import type_define
import error_codes

import datetime

class ApiQueryBirthdayEmployee(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        account_list = yield self.account_dao.query_account_list(field_type=type_define.TYPE_ACCOUNT_BIRTHDAY)
        data = {
            'today': [],
            'will': [],
            'retire': [],
        }
        for account in account_list:
            birthday = account['birthday']
            today = self.today()
            will = today + datetime.timedelta(days=self.settings['birthday_alert'])
            if birthday:
                this_birthday = datetime.date(year=today.year, month=birthday.month, day=birthday.day)
                if this_birthday == today:
                    data['today'].append(account)
                elif this_birthday > today and this_birthday <= will:
                    data['will'].append(account)
                if account['sex'] == type_define.TYPE_SEX_MALE:
                    retire_age = 60
                else:
                    if account['position_type'] == type_define.TYPE_POSITION_LEADER:
                        retire_age = 55
                    else:
                        retire_age = 50
                retire_day = datetime.date(year=birthday.year + retire_age, month=birthday.month, day=birthday.day)
                if today + datetime.timedelta(days=self.settings['retire_alert']) >= retire_day and today <= retire_day:
                    data['retire'].append(account)

        self.write_json({'status': error_codes.EC_SUCCESS, 'data': data})

