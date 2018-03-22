import os

import tornado.web
from tornado import ioloop
import tornado.options
from tornado.options import define, options
import platform

import handlers
import config

from db import account_dao, job_dao, config_dao, mysql_config, mysql_inst_mgr
from util.util import Util
import logging

define("mode", 1, int, "Enable debug mode, 3 is network debug, 2 is debug, 1 is network release, 0 is local release")
define("port", 5505, int, "Listen port")
define("address", "0.0.0.0", str, "Bind address")
system = platform.system()
if system == 'Windows':
    default_log_file = 'D:/log/oa.log'
elif system == 'Darwin':
    default_log_file = './log/oa.log'
else:
    default_log_file = '/data/log/oa/oa.log'
define('log_file', default_log_file, str, 'log file')
define('log_level', 'debug', str, 'log level')
options.parse_command_line()
log_level = options.log_level.lower()
if log_level == 'debug':
    log_level = logging.DEBUG
    config.enable_debug_log = True
elif log_level == 'warning':
    log_level = logging.WARNING
elif log_level == 'error':
    log_level = logging.ERROR
else:
    log_level = logging.INFO
Util.init_logging(options.log_file, log_level)

_mysql_config = mysql_config.MySQLConfig(mode=options.mode)
_mysql_inst_mgr = mysql_inst_mgr.MySQLInstMgr(metas=_mysql_config.global_metas)
_account_dao = account_dao.AccountDAO(_mysql_inst_mgr)
_job_dao = job_dao.JobDAO(_mysql_inst_mgr)
_config_dao = config_dao.ConfigDAO(_mysql_inst_mgr)
_job_timer = handlers.JobTimer(
    job_dao=_job_dao,
    account_dao=_account_dao,
    config_dao=_config_dao,
    auto_job_timeout=3,
    doc_timeout=5
)
try:
    from handlers.jpush_server import JpushServer
    _push_server = JpushServer()
except:
    _push_server = None

app = tornado.web.Application([
    (r'/res/(.*)', tornado.web.StaticFileHandler, {'path': "./template/res/"}),
    (r'/', handlers.IndexHandler),
    (r'/admin/operation', handlers.AdminOperation),
    (r'/admin', handlers.AdminOperation),
    (r'/login.html', handlers.LoginHandler),
    (r'/logout.html', handlers.LogoutHandler),
    (r'/api/update_account_info', handlers.ApiUpdateAccountInfo),
    (r'/api/update_password_protect_question', handlers.ApiUpdatePasswordPretectQuestion),
    (r'/api/get_password_protect_question', handlers.ApiGetPasswordProtectQuestion),
    (r'/api/update_login_phone', handlers.ApiUpdateLoginPhone),
    (r'/api/alter_account', handlers.ApiAlterAccount),
    (r'/api/query_account_list', handlers.ApiQueryAccountList),
    (r'/api/query_birthday_employee', handlers.ApiQueryBirthdayEmployee),
    (r'/api/alter_dept', handlers.ApiAlterDept),
    (r'/api/query_dept_list', handlers.ApiQueryDeptList),
    (r'/api/is_account_exist', handlers.ApiIsAccountExist),
    (r'/api/reset_password', handlers.ApiResetPassword),
    (r'/api/create_new_job', handlers.ApiCreateNewJob),
    (r'/api/upload_file', handlers.ApiUploadFile),
    (r'/api/send_official_doc', handlers.ApiSendOfficialDoc),
    (r'/api/query_job_list', handlers.ApiQueryJobList),
    (r'/api/query_job_info', handlers.ApiQueryJobInfo),
    (r'/api/alter_job', handlers.ApiAlterJob),
    (r'/api/alter_job_path', handlers.ApiAlterJobPath),
    (r'/api/query_job_path_info', handlers.ApiQueryJobPathInfo),
    (r'/api/process_auto_job', handlers.ApiProcessAutoJob),
    (r'/api/query_job_status_mark', handlers.ApiQueryJobStatusMark),
    (r'/api/job_memo', handlers.ApiJobMemo),
    (r'/api/query_account_extend', handlers.ApiQueryAccountExtend),
    (r'/api/outer_link', handlers.ApiOuterLinkHandler),
    (r'/api/download_type', handlers.ApiDownloadType),
    (r'/api/download_detail', handlers.ApiDownloadDetail),
    (r'/api/rule_type', handlers.ApiRuleType),
    (r'/api/rule_detail', handlers.ApiRuleDetail),
    (r'/api/common_config', handlers.ApiCommonConfig),
    (r'/api/operation_mask', handlers.ApiOperationMask),
    (r'/api/admin_reset_psd', handlers.ApiAdminResetPsd),
    (r'/api/leave_statistics', handlers.ApiLeaveStatistics),
    (r'/api/employee_statistics', handlers.ApiEmployeeStatistics),
    (r'/api/job_export', handlers.ApiJobExport),
    (r'/api/dynamic', handlers.ApiDynamic),
    (r'/api/fetch_my_info', handlers.ApiFetchMyInfo),
    (r'/api/query_leave_list', handlers.ApiQueryLeaveList),
    (r'/(.*)', handlers.HtmlHandler),
],
    test_mode=config.test_mode,
    autoreload=False,
    cookie_secret='a05e6ee50f9f0b5d7cbade2fee456874a',
    template_path=os.path.join(os.path.dirname(__file__), "template"),
    account_dao=_account_dao,
    job_dao=_job_dao,
    config_dao=_config_dao,
    push_server=_push_server,
    birthday_alert=14,
    retire_alert = 180,
    auto_next_timeout = 72,
    job_timer=_job_timer,
)

app.listen(options.port, options.address)
ioloop.IOLoop.current().start()