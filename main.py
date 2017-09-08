import os

import tornado.web
from tornado import ioloop
import tornado.options
from tornado.options import define, options

import handlers
import config

from db import account_dao, job_dao, config_dao, mysql_config, mysql_inst_mgr

define("mode", 0, int, "Enable debug mode, 2 is release, 1 is network debug, 0 is local debug")
define("port", 5505, int, "Listen port")
define("address", "0.0.0.0", str, "Bind address")

_mysql_config = mysql_config.MySQLConfig(mode=options.mode)
_mysql_inst_mgr = mysql_inst_mgr.MySQLInstMgr(metas=_mysql_config.global_metas)
_account_dao = account_dao.AccountDAO(_mysql_inst_mgr)
_job_dao = job_dao.JobDAO(_mysql_inst_mgr)
_config_dao = config_dao.ConfigDAO(_mysql_inst_mgr)

app = tornado.web.Application([
    (r'/res/(.*)', tornado.web.StaticFileHandler, {'path': "./template/res/"}),
    (r'/', handlers.IndexHandler),
    (r'/admin/operation', handlers.AdminOperation),
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
    (r'/(.*)', handlers.HtmlHandler),
],
    test_mode=config.test_mode,
    autoreload=False,
    cookie_secret='a05e6ee50f9f0b5d7cbade2fee456874a',
    template_path=os.path.join(os.path.dirname(__file__), "template"),
    account_dao=_account_dao,
    job_dao=_job_dao,
    config_dao=_config_dao,
    birthday_alert=14,
    retire_alert = 180,
)

app.listen(options.port, options.address)
ioloop.IOLoop.current().start()