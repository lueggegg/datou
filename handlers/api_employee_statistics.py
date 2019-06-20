# -*- coding: utf-8 -*-

from api_handler import ApiHandler
from tornado import gen
import error_codes
import datetime
import type_define

class ApiEmployeeStatistics(ApiHandler):

    @gen.coroutine
    def _real_deal_request(self):
        op = self.get_argument_and_check_it('op')
        if op == 'export':
            dept_id = self.get_argument('dept_id', None)
            account_list = yield self.account_dao.query_account_list(dept_id)
            account_list = self.del_invalid_employee(account_list)
            if not account_list:
                self.finish_with_error(error_codes.EC_SYS_ERROR, '没有数据')
            date_type = self.get_argument('type', None)
            if date_type == 'detail':
                path = self.generate_detail_info_table(account_list)
            else:
                path = self.generate_ratio_table(account_list)
            self.write_data(path)
        else:
            self.finish_with_error(error_codes.EC_ARGUMENT_ERROR, '操作类型错误')


    def del_invalid_employee(self, account_list):
        result = []
        for account in account_list:
            if account['dept'] != '测试专用':
                result.append(account)
        return result


    def generate_detail_info_table(self, account_list):
        fields = [
            ['账号', 'account', 0],
            ['姓名', 'name', 0],
            ['性别', 'sex', 1],
            ['籍贯', 'descent', 1],
            ['身份证号', 'id_card', 0],
            ['出生日期', 'birthday', 0],
            ['毕业时间', 'graduate_date', 1],
            ['参加工作时间', 'work_begin_date', 1],
            ['入职时间', 'join_date', 1],
            ['合同结束时间', 'contract_end_date', 1],
            ['最高学历', 'education_level', 1],
            ['毕业院校及专业', 'college', 1],
            ['最高学位', 'degree', 1],
            ['学习形式', 'education_type', 1],
            ['技术职称', 'technical_title', 1],
            ['婚姻状况', 'marriage', 1],
            ['政治面貌', 'politics', 1],
            ['干部或职工', 'leadership', 1],
            ['现工作岗位', 'position', 1],
            ['部门', 'dept', 0],
            ['编制类型', 'authorized_strength', 1],
        ]
        data = [field[0] for field in fields]
        data.insert(0, '序号')
        data = [data]
        index = 0
        for account in account_list:
            index += 1
            line = [index]
            extend_info = self.loads_json(account['extend']) if account['extend'] else None
            for field in fields:
                element = extend_info[field[1]] if field[2] else account[field[1]]
                # if isinstance(element, datetime.date):
                #     element = element.strftime('%Y年%m月%d日')
                if field[1] == 'id_card':
                    element = 'ID_' + element
                line.append(element if element else '')
            data.append(line)
        path = self.generate_excel_file(data, 'employee_detail')
        return path


    def generate_ratio_table(self, account_list):
        size = len(account_list)
        data = [
            ['总人数', '集团派出领导', '事业编制', '企业编制', '临聘员工', '劳务员工'],
            [size, 0, 0, 0, 0, 0],
            ['占比(%)', 0, 0, 0, 0, 0],
            [],
            ['公司领导', '中层干部', '一级主管', '二级主管', '一级员工', '临聘员工', '劳务员工'],
            [0, 0, 0, 0, 0, 0, 0],
            [],
            ['年龄', '25岁以下', '25-34岁', '35-44岁', '45-50岁', '50岁以上'],
            ['男', 0, 0, 0, 0, 0],
            ['占比(%)', 0, 0, 0, 0, 0],
            ['女', 0, 0, 0, 0, 0],
            ['占比(%)', 0, 0, 0, 0, 0],
            [],
            ['学历', '博士研究生', '硕士研究生', '本科', '大专', '高中或中专', '初中', '其他'],
            ['人数', 0, 0, 0, 0, 0, 0, 0],
            [],
            ['职称', '高级', '中级', '助理', '无'],
            ['人数', 0, 0, 0, 0],
            [],
            ['政治面貌', '中共党员', '共青团员', '群众', '其他'],
            ['人数', 0, 0, 0, 0],
            [],
            ['部门', '公司领导'],
            ['人数', 0],
        ]
        sub_table_begin_line = [0]
        ratio_lines = []
        index = 0
        for line in data:
            if not line:
                sub_table_begin_line.append(index + 1)
            elif isinstance(line[0], str) and '%' in line[0]:
                ratio_lines.append(index)
            index += 1
        today = self.today()
        for account in account_list:
            extend_info = self.loads_json(account['extend']) if account['extend'] else None
            sub_table_index = 0
            begin_line = sub_table_begin_line[sub_table_index]
            authorized_list = data[begin_line]
            data_line = data[begin_line + 1]
            for i in range(1, len(authorized_list)):
                if authorized_list[i] in extend_info['authorized_strength']:
                    data_line[i] += 1
                    break
            sub_table_index += 1
            begin_line = sub_table_begin_line[sub_table_index]
            position_list = data[begin_line]
            position = account['position']
            data_line = data[begin_line + 1]
            if position in ['台长', '副台长', '财务总监']:
                data_line[0] += 1
            elif position in ['主任', '副主任', '编委']:
                data_line[1] += 1
            else:
                for i in range(2, len(position_list)):
                    if position == position_list[i]:
                        data_line[i] += 1
                        break
            sub_table_index += 1
            begin_line = sub_table_begin_line[sub_table_index]
            age = self.get_age(account['birthday'], today)
            data_line = data[begin_line + 1] if account['sex'] == type_define.TYPE_SEX_MALE else data[begin_line + 3]
            self.set_age_count(data_line, age)
            sub_table_index += 1
            begin_line = sub_table_begin_line[sub_table_index]
            level_list = data[begin_line]
            data_line = data[begin_line + 1]
            if not extend_info['education_level']:
                data_line[len(level_list) - 1] += 1
            else:
                for i in range(1, len(level_list)-1):
                    if extend_info['education_level'] in level_list[i]:
                        data_line[i] += 1
                        break
            sub_table_index += 1
            begin_line = sub_table_begin_line[sub_table_index]
            level_list = data[begin_line]
            data_line = data[begin_line + 1]
            title_level = extend_info['technical_title_level']
            for i in range(1, len(level_list)):
                if title_level == level_list[i]:
                    data_line[i] += 1
                    break
            sub_table_index += 1
            begin_line = sub_table_begin_line[sub_table_index]
            politics_list = data[begin_line]
            data_line = data[begin_line + 1]
            politics = extend_info['politics']
            if not politics:
                data_line[len(politics_list) - 1] += 1
            else:
                for i in range(1, len(politics_list)):
                    if politics in politics_list[i]:
                        data_line[i] += 1
                        break
            sub_table_index += 1
            begin_line = sub_table_begin_line[sub_table_index]
            dept_list = data[begin_line]
            data_line = data[begin_line + 1]
            dept = account['dept']
            if position in ['台长', '副台长']:
                data_line[1] += 1
            elif dept not in dept_list:
                dept_list.append(dept)
                data_line.append(1)
            else:
                for i in range(2, len(dept_list)):
                    if dept == dept_list[i]:
                        data_line[i] += 1
        for line in ratio_lines:
            ratio_line = data[line]
            data_line = data[line - 1]
            for i in range(1, len(data_line)):
                ratio_line[i] = '%.2f' % (float(data_line[i])/size * 100,)
        path = self.generate_excel_file(data, 'employee_ratio')
        return path


    def get_age(self, birthday, today=None):
        if not isinstance(birthday, datetime.date):
            return 0
        if not today:
            today = self.today()
        offset = 0 if today.month >= birthday.month and today.day >- birthday.month else -1
        return today.year - birthday.year + offset

    def set_age_count(self, data_line, age):
        index = 1
        divider = [25, 35, 45, 51]
        for item in divider:
            if age >= item:
                index += 1
            else:
                break
        data_line[index] += 1





