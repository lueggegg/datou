// generated by script, do not edit it yourself


var TYPE_EMPLOYEE_NORMAL = 0;
var TYPE_EMPLOYEE_TRAINEE = 1;
var TYPE_EMPLOYEE_RESIGN = 2;

var TYPE_ACCOUNT_NORMAL = 0;
var TYPE_ACCOUNT_CONTACT = 1;
var TYPE_ACCOUNT_SAMPLE = 2;
var TYPE_ACCOUNT_LEADER = 3;
var TYPE_ACCOUNT_BIRTHDAY = 4;
var TYPE_ACCOUNT_OPERATION_MASK = 5;
var TYPE_ACCOUNT_JUST_ID = 6;

var TYPE_POSITION_NORMAL = 0;
var TYPE_POSITION_LEADER = 1;

var TYPE_JOB_ADMIN = 0;
var TYPE_JOB_ADMIN_RESET_PSD = 1;


var TYPE_JOB_BEGIN = 0;
var TYPE_JOB_OFFICIAL_DOC = 1;
var TYPE_JOB_CERTIFICATE_SALARY = 2;
var TYPE_JOB_CERTIFICATE_LABOR = 3;
var TYPE_JOB_CERTIFICATE_MARRIAGE = 4;
var TYPE_JOB_CERTIFICATE_INTERNSHIP = 5;
var TYPE_JOB_HR_RESIGN = 6;
var TYPE_JOB_HR_RECOMMEND = 7;
var TYPE_JOB_HR_ANOTHER_POST = 8;
var TYPE_JOB_HR_ASK_FOR_LEAVE = 9;
var TYPE_JOB_FINANCIAL_PURCHASE = 10;
var TYPE_JOB_FINANCIAL_REIMBURSEMENT = 11;
var TYPE_JOB_HR_LEAVE_FOR_BORN = 12;
var TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY = 13;
var TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY = 14;
var TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY = 15;
var TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY = 16;
var TYPE_JOB_LEAVE_FOR_BORN_LEADER = 17;
var TYPE_JOB_LEAVE_FOR_BORN_NORMAL = 18;
var TYPE_JOB_DOC_REPORT = 19;
var TYPE_JOB_APPLY_RESET_PSD = 20;
var TYPE_JOB_CUSTOM_NEW = 21;
var TYPE_JOB_SYSTEM_MSG = 22;
var TYPE_JOB_DYNAMIC = 23;
var TYPE_JOB_END = 24;

var TYPE_JOB_SUB_TYPE_BRANCH = 1;
var TYPE_JOB_SUB_TYPE_GROUP = 2;
var TYPE_JOB_OFFICIAL_DOC_BRANCH = 1;
var TYPE_JOB_OFFICIAL_DOC_GROUP = 2;
var TYPE_JOB_DOC_REPORT_BRANCH = 1;
var TYPE_JOB_DOC_REPORT_GROUP = 2;

var TYPE_JOB_SYSTEM_MSG_SUB_TYPE_BIRTHDAY = 1;
var TYPE_JOB_SYSTEM_MSG_SUB_TYPE_CANCEL_JOB = 2;
var TYPE_JOB_SYSTEM_MSG_SUB_TYPE_OTHER=100;

var TYPE_JOB_QUERY_AUTO_JOB = 1;
var TYPE_JOB_QUERY_DOC_REPORT = 2;
var TYPE_JOB_QUERY_NOTIFY_AUTO_JOB = 3;
var TYPE_JOB_QUERY_NOTIFY_DOC_REPORT = 4;
var TYPE_JOB_QUERY_NOTIFY_SYS_MSG = 5;
var TYPE_JOB_QUERY_SYS_MSG = 6;
var TYPE_JOB_QUERY_DYNAMIC = 7;

var TYPE_JOB_NODE_NORMAL = 0;
var TYPE_JOB_NODE_REMIND_COMPLETE = 1;
var TYPE_JOB_NODE_TIMEOUT = 2;
var TYPE_JOB_NODE_SYS_MSG = 3;
var TYPE_JOB_NODE_COMMENT = 4;

var TYPE_JOB_NOTIFY_AUTO_JOB = 1;
var TYPE_JOB_NOTIFY_DOC_REPORT = 2;
var TYPE_JOB_NOTIFY_SYS_MSG = 3;

var TYPE_JOB_ATTACHMENT_NORMAL = 0;
var TYPE_JOB_ATTACHMENT_IMG = 1;
var TYPE_UPLOAD_FILE_TO_DOWNLOAD = 2;
var TYPE_UPLOAD_RULE_FILE = 3;
var TYPE_UPLOAD_BIRTHDAY_IMG = 4;
var TYPE_UPLOAD_COMMON_IMG = 5;


var TYPE_NEWS_LINK_IMG = 1;
var TYPE_NEWS_LINK_COMPANY = 2;
var TYPE_NEWS_LINK_OTHER = 3;
var TYPE_USEFUL_LINK = 4;

var TYPE_DOWNLOAD_FILE = 1;
var TYPE_DOWNLOAD_RULE = 2;

var TYPE_CONFIG_DEPT_LEVEL_NAME = 1;
var TYPE_CONFIG_BIRTHDAY_WISHES = 2;

var TYPE_CONFIG_KEY_DEPT_LEVEL_FIRST = 1;
var TYPE_CONFIG_KEY_DEPT_LEVEL_MAX = 5;
var TYPE_CONFIG_KEY_BIRTHDAY_WISHES_TITLE = 1;
var TYPE_CONFIG_KEY_BIRTHDAY_WISHES_CONTENT = 2;
var TYPE_CONFIG_KEY_BIRTHDAY_WISHES_IMG = 3;

var TYPE_SEX_MALE = 0;
var TYPE_SEX_FEMALE = 1;

var TYPE_REPORT_TO_LEADER_TILL_CHAIR = 3;
var TYPE_REPORT_TO_LEADER_TILL_VIA = 4;
var TYPE_REPORT_TO_LEADER_TILL_DEPT = 5;
var TYPE_REPORT_CONTINUE_TILL_VIA = 6;
var TYPE_REPORT_CONTINUE_TILL_CHAIR = 7;

var STATUS_EMPLOYEE_INVALID = 0;
var STATUS_EMPLOYEE_NORMAL = 1;
var STATUS_EMPLOYEE_SYSTEM = 2;
var STATUS_EMPLOYEE_RETIRE = 3;
var STATUS_EMPLOYEE_RESIGN = 4;
var STATUS_EMPLOYEE_TRAINEE = 5;


var STATUS_JOB_INVALID = 0;
var STATUS_JOB_PROCESSING = 1;
var STATUS_JOB_COMPLETED = 2;
var STATUS_JOB_REJECTED = 3;
var STATUS_JOB_CANCEL = 4;
var STATUS_JOB_SYS_CANCEL = 5;

var STATUS_JOB_INVOKED_BY_MYSELF = 0;
var STATUS_JOB_MARK_WAITING = 1;
var STATUS_JOB_MARK_PROCESSED = 2;
var STATUS_JOB_MARK_COMPLETED = 3;
var STATUS_JOB_MARK_NEW_REPLY = 4;
var STATUS_JOB_MARK_SYS_MSG = 5;


var STATUS_BROADCAST_WOULD_START = 1;
var STATUS_BROADCAST_STARTED = 2;
var STATUS_BROADCAST_NOT_EXCEED = 3;
var STATUS_BROADCAST_EXCEED = 4;

var AUTHORITY_DEVELOPER = 0;
var AUTHORITY_SUPER_ADMIN = 1;
var AUTHORITY_ADMIN = 8;
var AUTHORITY_CHAIR_LEADER = 16;
var AUTHORITY_VIA_LEADER = 32;
var AUTHORITY_DEPT_LEADER = 128;


var OPERATION_MASK_EMPLOYEE = 16;
var OPERATION_MASK_INDEX_PAGE = 32;
var OPERATION_MASK_RULE = 64;
var OPERATION_MASK_DOWNLOAD_FILE = 128;
var OPERATION_MASK_QUERY_AUTO_JOB = 256;
var OPERATION_MASK_QUERY_REPORT = 512;
var OPERATION_MASK_COMMENT_LEAVE = 1024;
var OPERATION_MASK_LEAVE_LIST_PROMPT = 2048;

