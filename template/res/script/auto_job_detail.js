var main_info;
var node_list_data;

var left_comment_dlg;

$(document).ready(init);

function init() {
    if (!isAuthorized(OPERATION_MASK_QUERY_AUTO_JOB)) {
        commonPost('/api/query_job_info', {type: 'authority', job_id: __job_id}, function (data) {
            if (!data) {
                redirectError('没有权限');
            }
        });
    }

    if (__notify) {
        commonPost('/api/alter_job', {job_id: __job_id, op: 'notify_read'}, function (data) {

        });
    }

    $("#process_container").hide();

    $("#comment_btn").hide();
    left_comment_dlg = $("#left_comment_dlg");
    left_comment_dlg.hide();

    queryJobBaseInfo();

    initConfirmDialog();
}

function initProcessContainer() {
    $("#doc_send_btn").click(function (event) {
        reply();
    });
    $("#doc_reject_btn").click(function (event) {
        showConfirmDialog('拒绝该申请并归档该工作流？', function () {
            commonPost('/api/process_auto_job',
                {job_id: __job_id, job_type: main_info.type, op: 'reject', content: wrapJobContent($("#doc_content").val())},
                function (data) {
                promptMsg('操作成功，2s后自动刷新...');
                setTimeout(function () {
                    refresh();
                }, 2000);
            });
        })
    });
}

function isLeftJob(type) {
    return type === TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY ||
        type === TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY ||
        type === TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY ||
        type === TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY ||
        type === TYPE_JOB_LEAVE_FOR_BORN_NORMAL ||
        type === TYPE_JOB_LEAVE_FOR_BORN_LEADER;
}

function queryJobBaseInfo() {
    commonPost('/api/query_job_info', {type: 'base', job_id: __job_id}, function (data) {
        main_info = data;
        $("#doc_topic").text(main_info.title);
        $('title').text(job_type_map[main_info.type]);
        if (main_info.status !== STATUS_JOB_PROCESSING) {
            var status = {};
            status[STATUS_JOB_COMPLETED] = '已完成';
            status[STATUS_JOB_REJECTED] = '未通过';
            status[STATUS_JOB_CANCEL] = '已撤回';
            status[STATUS_JOB_SYS_CANCEL] = '系统撤回';
            $("#cancel_btn").remove();
            $("#job_status").text(status[main_info.status]);
            initExport();
            if (main_info.status === STATUS_JOB_COMPLETED && isLeftJob(main_info.type) && isAuthorized(OPERATION_MASK_COMMENT_LEAVE)) {
                left_comment_dlg.show();
                commonInitLeftSpinner($("#real_left_days"));
                commonPost('/api/process_auto_job', {job_id: __job_id, op: 'query_leave_detail'}, function (data) {
                    if (data) {
                        $("#real_left_days").spinner('value', data.half_day * 0.5);
                    } else {
                        $("#real_left_days").spinner('value', 0);
                    }
                });
                commonInitDialog(left_comment_dlg, function () {
                    var half_day = getHalfDaysFromSpinner($("#real_left_days"));
                    var comment = $("#left_comment").val();
                    if (!comment) {
                        promptMsg("请输入备注内容");
                        return;
                    }
                    comment = '【实际请假{*' + (half_day*0.5) + '*}天】\n' + comment;
                    commonPost('/api/process_auto_job',
                        {job_id: __job_id, op: 'left_comment', half_day: half_day, comment: wrapJobContent(comment), 'node_type': TYPE_JOB_NODE_COMMENT},
                        function (data) { window.location.reload();});
                }, {width: 640});
                var comment_btn = $("#comment_btn");
                comment_btn.show();
                comment_btn.click(function () {
                    left_comment_dlg.dialog("open");
                });
            }
        } else {
            $("#job_status").text('处理中');
            $("#export_btn").remove();
            if (main_info.invoker !== __my_uid) {
                $("#cancel_btn").remove();
            } else {
                $("#cancel_btn").click(function (event) {
                    showConfirmDialog('撤消该工作流？', function () {
                        commonPost('/api/process_auto_job', {op: 'cancel', job_id: __job_id, job_type: main_info.type}, function (data) {
                            promptMsg('撤消成功，2s后自动刷新...');
                            setTimeout(function () {
                                refresh();
                            }, 2000);
                        });
                    });
                });
            }
        }
        queryJobNodeList();
    });
}

function initExport() {
    $("#export_btn").click(function () {
        commonPost('/api/job_export', {op: 'single', job_id: __job_id}, function (data) {
            window.open(data);
        });
    });
}

function queryJobNodeList() {
    commonPost('/api/query_job_info', {type: 'node', job_id: __job_id}, function(data) {
        node_list_data = data;
        var last_node;
        data.forEach(function (p1, p2, p3) {
            addJobNodeItem(p1, p2);
            last_node = p1;
        });
        if (main_info.status === STATUS_JOB_PROCESSING) {
            commonPost('/api/query_job_status_mark', {job_id: __job_id}, function (data) {
                if (data && data.status === STATUS_JOB_MARK_WAITING) {
                    $("#process_container").show();
                    initProcessContainer();
                } else {
                    commonPost('/api/process_auto_job', {op: 'query_cur', job_id: __job_id, cur_path_index: main_info.cur_path_index}, function (data) {
                        var fake_node = {
                            id: -1,
                            account: 'system',
                            sender: 'system',
                            dept: '后台',
                            has_attachment: 0,
                            has_img: 0,
                            time: '待定'
                        };
                        var content = '{*【以下员工，待处理该工作流：】*}\n';
                        var divider = getDoubleSpace(2);
                        data.forEach(function (p1, p2, p3) {
                            content += divider + p1.dept + divider + p1.account + divider + p1.name + '\n';
                        });
                        fake_node['content'] = wrapJobContent(content);
                        addJobNodeItem(fake_node, node_list_data.length, true);
                    });
                }
            });
        }
    });
}

function addJobNodeItem(node_data, index, fake) {
    fake = !!fake;
    var html = "<div class='node_item_container'>";
    var comment_label = '';
    if (fake) {
        html += "<div class='fake_node_item_header'>";
    } else if (node_data.type === TYPE_JOB_NODE_TIMEOUT || node_data.type === TYPE_JOB_NODE_SYS_MSG) {
        html += "<div class='timeout_node_item_header'>";
    } else if (node_data.type === TYPE_JOB_NODE_COMMENT) {
        html += "<div class='comment_node_item_header'>";
        comment_label += "<div class='comment_node_label'>备注</div>";
    } else {
        if (index % 2) {
            html += "<div class='node_item_header_even'>";
        } else {
            html += "<div class='node_item_header'>";
        }
    }
    var header_data = [[
        "工号：" + node_data.account,
        "姓名：" + node_data.sender,
        "部门：" + node_data.dept,
        "<div class='node_item_header_time'>" + node_data.time + "</div>"
    ]];
    html += getListViewHtml(header_data, {weight: [1, 1, 1, 1.5], without_title: true, diff_background: false, ul_class: 'node_item_header_ul'});
    html += "</div>";
    if (node_data.has_attachment) {
        html += "<div class='node_item_attachment'>附件：";
        html += "<ul>";
        node_data.attachment.forEach(function (p1, p2, p3) {
            html += "<li><a target='_blank' href='" + p1.path + "'>" + p1.name + "</a></li>";
        });
        html += "</ul></div>";
    }
    // if (node_data.type === TYPE_JOB_NODE_REMIND_COMPLETE) {
    //     html += "<div class='sp_type_info'>【审阅者提醒：归档该公文】</div>";
    // }
    html += "<div class='node_item_content' id='node_item_content_" + node_data.id + "'></div>";
    html += "</div>";
    $("#doc_node_list").append(html);
    var img_list_html = '';
    if (node_data.has_img) {
        img_list_html += "<ul>";
        node_data.img_attachment.forEach(function (p1, p2, p3) {
            img_list_html += "<li><img src='" + p1.path + "'></li>";
        });
        img_list_html += "</ul>";
    }
    $("#node_item_content_" + node_data.id).html(comment_label + img_list_html + '<div>' + parseJobContent(node_data.content) + '</div>');
}

function reply() {
    var content = $("#doc_content").val();
    var param = {
        content: wrapJobContent(content),
        job_id: __job_id,
        op: 'reply',
        job_type: main_info.type
    };

    commonPost('/api/process_auto_job', param, function (data) {
        promptMsg('回复成功，2s后自动刷新...');
        setTimeout(function () {
            refresh();
        }, 2000);
    });
}

function refresh() {
    window.location.reload();
}