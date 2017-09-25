
$(document).ready(function () {
    $("#inline_date").datepicker();

    queryImgNews();
    queryTextNews();
    queryUsefulLink();
    queryWaitingJob();
    queryRecentJob();
    queryBirthdayEmployee();
    queryCompletedJob();
    queryCompletedDocReport();
});

var img_news = null;
var current_img_index = 0;
var img_size = 0;

var mark_status_map = {};
mark_status_map[STATUS_JOB_MARK_COMPLETED] = '已归档';
mark_status_map[STATUS_JOB_MARK_WAITING] = '待办';
mark_status_map[STATUS_JOB_MARK_PROCESSED] = '已处理';
mark_status_map[STATUS_JOB_INVOKED_BY_MYSELF] = '我发起';

function queryImgNews() {
    commonPost('/api/outer_link', {op: 'query', type: TYPE_NEWS_LINK_IMG}, function (data) {
        img_news = data;
        img_size = img_news.length;
        if (img_size !== 0) {
            showCurrentImgNews();
        }
        if (img_size > 1) {
            looperNewImg(3000);
        }
    });
}

function queryTextNews() {
    var types =[
        [TYPE_NEWS_LINK_COMPANY, $("#company_news_list")],
        [TYPE_NEWS_LINK_OTHER, $("#other_news_list")]
    ];
    types.forEach(function (p1, p2, p3) {
        commonPost('/api/outer_link', {op: 'query', type: p1[0], count: 5}, function (data) {
            if (data.length === 0) {
                p1[1].append('<li>没有要闻</li>');
            } else {
                var list = '';
                data.forEach(function (item, index, p) {
                    list += "<li><a target='_blank' title='" + item.title + "' href='" + item.url +"'>" + item.title + "</a></li>";
                });
                p1[1].append(list);
            }
        })
    });
}

function queryUsefulLink() {
    commonPost('/api/outer_link', {op: 'query', type: TYPE_USEFUL_LINK}, function (data) {
        if (data.length > 0) {
            var html = "<div class='index_news_divider'></div><div class='topic_title'>常用链接</div>";
            html += "<ul class='base_ul'>";
            data.forEach(function (item, p2, p3) {
                html += "<li><a target='_blank' title='" + item.title + "' href='" + item.url +"'>" + item.title + "</a></li>";
            });
            html += "</ul>";
            $("#useful_link_container").append(html);
        }
    });
}

function looperNewImg(millis) {
    setTimeout(function () {
        current_img_index++;
        if (current_img_index === img_size) {
            current_img_index = 0;
        }
        showCurrentImgNews();
        looperNewImg(millis);
    }, millis);
}

function showCurrentImgNews() {
    var item = img_news[current_img_index];
    $("#img_news_img").attr('src', item.img_url);
    $("#img_news_title").text(item.title);
    $("#img_news_url").attr('href', item.url);
    $("#img_news_url").attr('title', item.title);
}

function queryWaitingJob() {
    commonPost('/api/query_job_list', {status: STATUS_JOB_MARK_WAITING}, function (data) {
        if (data.length === 0) {
            $("#waiting_job_container").hide();
        } else {
            var list = '';
            data.forEach(function (p1, p2, p3) {
                list += '<li><div class="element_left recent_info_type" >[' + job_type_map[p1.type] + ']</div>';
                list += '<div class="recent_info_mark_status">' + getMarkStatusLabel(p1.mark_status, p1.sub_type) + '</div>';
                list += '<div class="waiting_job_main"><a target="_blank" href="'
                    + getJobUrl(p1.type, p1.job_id, p1.branch_id) + '" title="' + p1.title + '">' + p1.title + '</a></div>';
                list += '</li>';
            });
            $("#waiting_job_list").append(list);
        }
    });
}

function queryRecentJob() {
    commonPost('/api/query_job_list', {count: 10}, function (data) {
        if (data.length > 0) {
            $("#empty_job_container").hide();
            var job_status = {};
            job_status[STATUS_JOB_PROCESSING] = '<span style="color: orange">处理中</span>';
            job_status[STATUS_JOB_COMPLETED] = '<span style="color: rgb(0,225,32)">已完成</span>';
            job_status[STATUS_JOB_REJECTED] = '<span style="color: red">未通过</span>';
            job_status[STATUS_JOB_CANCEL] = '<span style="color: gray">被撤回</span>';
            var list = '';
            data.forEach(function (p1, p2, p3) {
                list += '<li>';
                list += '<div class="recent_info_type">[' + job_type_map[p1.type] + ']</div>';
                list += '<div class="recent_info_mark_status">' + getMarkStatusLabel(p1.mark_status, p1.sub_type) + '</div>';
                list += '<div class="recent_info_status">' + job_status[p1.job_status] + '</div>';
                list += '<div class="recent_info_main"><a target="_blank" href="'
                    + getJobUrl(p1.type, p1.job_id, p1.branch_id) + '" title="' + p1.title + '">' + p1.title + '</a></div>';
                list += '</li>';
            });
            $("#recent_job_list").append(list);
        }
    });
}

function queryCompletedJob() {
    var container = $("#completed_job_container");
    if (__authority > __admin_authority && (__my_operation_mask & OPERATION_MASK_QUERY_AUTO_JOB) === 0) {
        container.hide();
    } else {
        commonPost('/api/query_job_list', {query_type: TYPE_JOB_QUERY_NOTIFY_AUTO_JOB}, function (data) {
            if (data.length > 0) {
                var job_status = {};
                job_status[STATUS_JOB_PROCESSING] = '<span style="color: orange">处理中</span>';
                job_status[STATUS_JOB_COMPLETED] = '<span style="color: rgb(0,225,32)">已完成</span>';
                job_status[STATUS_JOB_REJECTED] = '<span style="color: red">未通过</span>';
                job_status[STATUS_JOB_CANCEL] = '<span style="color: gray">被撤回</span>';
                var list = '';
                data.forEach(function (p1, p2, p3) {
                    list += '<li>';
                    list += '<div class="recent_info_type">[' + job_type_map[p1.type] + ']</div>';
                    list += '<div class="recent_info_status">' + job_status[p1.job_status] + '</div>';
                    list += '<div class="recent_info_main"><a target="_blank" href="'
                        + getJobUrl(p1.type, p1.id, null, 1) + '" title="' + p1.title + '">' + p1.title + '</a></div>';
                    list += '</li>';
                });
                $("#completed_job_list").append(list);
            } else {
                $("#completed_job_list").append('<li>　暂无新归档的工作流</li>');
            }
        });
    }
}

function queryCompletedDocReport() {
    var container = $("#completed_job_container");
    if (__authority > __admin_authority && (__my_operation_mask & OPERATION_MASK_QUERY_REPORT) === 0) {
        container.hide();
    } else {
        commonPost('/api/query_job_list', {query_type: TYPE_JOB_QUERY_NOTIFY_DOC_REPORT}, function (data) {
            if (data.length > 0) {
                var job_status = {};
                job_status[STATUS_JOB_PROCESSING] = '<span style="color: orange">处理中</span>';
                job_status[STATUS_JOB_COMPLETED] = '<span style="color: rgb(0,225,32)">已完成</span>';
                job_status[STATUS_JOB_REJECTED] = '<span style="color: red">未通过</span>';
                job_status[STATUS_JOB_CANCEL] = '<span style="color: gray">被撤回</span>';
                var list = '';
                data.forEach(function (p1, p2, p3) {
                    list += '<li>';
                    list += '<div class="recent_info_type">[' + job_type_map[p1.type] + ']</div>';
                    list += '<div class="recent_info_status">' + job_status[p1.job_status] + '</div>';
                    list += '<div class="recent_info_main"><a target="_blank" href="'
                        + getJobUrl(p1.type, p1.id, null, 1) + '" title="' + p1.title + '">' + p1.title + '</a></div>';
                    list += '</li>';
                });
                $("#completed_doc_report_list").append(list);
            } else {
                $("#completed_doc_report_list").append('<li>　暂无新归档的呈报表</li>');
            }
        });
    }
}

function getMarkStatusLabel(mark_status, job_sub_type) {
    if (job_sub_type === TYPE_JOB_SUB_TYPE_GROUP && mark_status === STATUS_JOB_MARK_WAITING) {
        return '新消息';
    }
    return mark_status_map[mark_status];
}

function getJobUrl(job_type, job_id, branch_id, notify) {
    var url;
    switch (job_type) {
        case TYPE_JOB_OFFICIAL_DOC:
        case TYPE_JOB_DOC_REPORT:
            url =  'doc_detail.html?job_id=' + job_id;
            if (branch_id) {
                url += '&branch_id=' + branch_id;
            }
            break;
        default:
            url = 'auto_job_detail.html?job_id=' + job_id + "&title=" + encodeURI(job_type_map[job_type]);
            break;
    }
    if (notify) {
        url += '&notify=1';
    }
    return url;
}

function queryBirthdayEmployee() {
    ['today', 'will', 'retire'].forEach(function (p1, p2, p3) {
        $("#" + p1 + "_birthday_container").hide();
    });
    if (__authority > __admin_authority && (__my_operation_mask & OPERATION_MASK_EMPLOYEE) === 0) {
        return;
    }
    commonPost('/api/query_birthday_employee', null, function (data) {
        var title = ['工号', '姓名', '部门', '生日'];
        ['today', 'will', 'retire'].forEach(function (p1, p2, p3) {
            var accounts = data[p1];
            if (accounts.length > 0) {
                var list_data = [];
                accounts.forEach(function (account, index, p) {
                    list_data.push([
                        '<a target="_blank" href="employee_info_table.html?op=update&uid=' + account.id + '">' + account.account + '</a>',
                        account.name,
                        account.dept,
                        account.birthday
                    ]);
                });
                $("#" + p1 + "_birthday_container").show();
                updateListView($("#" + p1 + "_birthday_list"), list_data, {without_title: true});
            }
        });
    });
}