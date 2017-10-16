var job_list_container = [];
var job_types = [];

var invoker_select_dlg;
var invoker_select_controller;

var report_invoker_select_dlg;
var report_invoker_select_controller;

$(document).ready(function () {
    verticalTabs();

    job_list_container.push(
        $("#job_waiting"),
        $("#job_processed"),
        $("#job_completed"),
        $("#job_sent_by_myself"),
        $("#job_list_container"),
        $("#doc_report_list_container")
    );
    job_types.push(
        STATUS_JOB_MARK_WAITING,
        STATUS_JOB_MARK_PROCESSED,
        STATUS_JOB_MARK_COMPLETED,
        STATUS_JOB_INVOKED_BY_MYSELF
    );

    for (var i in job_types) {
        queryJobList(i);
    }

    document.onkeydown = function (e) {
        if (e.keyCode === 13) {
            onQueryBtnClick();
        }
    };

    decideAutoJobQueryOperation();
    decideDocReportQueryOperation();
    decideAdminJobOperation();
});

function decideAutoJobQueryOperation() {
    invoker_select_dlg = $("#select_invoker_dlg");
    if (__authority <= __admin_authority || (__my_operation_mask & OPERATION_MASK_QUERY_AUTO_JOB)) {
        var type_options = '';
        [
            TYPE_JOB_HR_ASK_FOR_LEAVE,
            TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY,
            TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY,
            TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY,
            TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY,
            TYPE_JOB_HR_LEAVE_FOR_BORN,
            TYPE_JOB_LEAVE_FOR_BORN_LEADER,
            TYPE_JOB_LEAVE_FOR_BORN_NORMAL,
            TYPE_JOB_HR_RESIGN,
            TYPE_JOB_FINANCIAL_PURCHASE
        ].forEach(function (p1, p2, p3) {
            type_options += '<option value="' + p1 + '">' + job_type_map[p1] + '</option>';
        });
        var container = $("#auto_job_type");
        container.append(type_options);
        selectMenu(container);

        commonInitDialog(invoker_select_dlg, onInvokerSelected, {width: 720});
        invoker_select_controller = createEmployeeMultiSelectorController($("#employee_selectable_container"));
        $("#add_invoker_btn").click(openInvokerSelectDlg);

        initDatePicker($("#invoke_begin"));
        initDatePicker($("#invoker_end"));

        selectMenu($("#leave_type"));
        commonPost('/api/query_dept_list', {pure: 1}, function (data) {
            var options = '';
           data.forEach(function (p1, p2, p3) {
               options += '<option value="' + p1.id + '">' + p1.name + '</option>';
           }) ;
           var container = $("#leave_dept");
           container.append(options);
           selectMenu(container);
        });
        initDatePicker($("#min_begin_time"));
        initDatePicker($("#max_begin_time"));
    } else {
        $("#query_job_tab").hide();
        $("#query_job_container").hide();
        invoker_select_dlg.hide();

        $("#query_leave_detail").hide();
        $("#query_leave_detail_container").hide();
    }
}

function openInvokerSelectDlg() {
    invoker_select_dlg.dialog('open');
    invoker_select_controller.fresh();
}

function onInvokerSelected() {
    var container = $("#invoker_list");
    removeChildren(container);
    var rec_set = invoker_select_controller.get_result();
    var list_data = '';
    var employee_map = invoker_select_controller.employee_map;
    rec_set.forEach(function (p1, p2, p3) {
        var employee = employee_map[p1];
        list_data += '<li value="' + p1 + '">' + employee.name + ';';
        list_data += '<img class="common_small_del_btn" src="res/images/icon/gray_del.png" onclick="delInvoner(' + p1 + ')">';
        list_data += '</li>';
    });
    container.append(list_data);
    invoker_select_dlg.dialog('close');
}

function delInvoner(uid) {
    $("#invoker_list [value='" + uid + "']").remove();
    invoker_select_controller.remove_item(uid);
}

function decideDocReportQueryOperation() {
    report_invoker_select_dlg = $("#select_report_invoker_dlg");
    if (__authority <= __admin_authority || (__my_operation_mask & OPERATION_MASK_QUERY_REPORT)) {
        var type_options = '';
        [
            TYPE_JOB_OFFICIAL_DOC,
            TYPE_JOB_DOC_REPORT
        ].forEach(function (p1, p2, p3) {
            type_options += '<option value="' + p1 + '">' + job_type_map[p1] + '</option>';
        });
        var container = $("#doc_type");
        container.append(type_options);
        selectMenu(container);

        selectMenu($("#doc_status"));

        commonInitDialog(report_invoker_select_dlg, onReportInvokerSelected, {width: 720});
        report_invoker_select_controller = createEmployeeMultiSelectorController($("#report_employee_selectable_container"));
        $("#add_report_invoker_btn").click(openReportInvokerSelectDlg);

        initDatePicker($("#report_invoke_begin"));
        initDatePicker($("#report_invoker_end"));

    } else {
        $("#query_report_tab").hide();
        $("#query_doc_report_container").hide();
        report_invoker_select_dlg.hide();
    }
}

function openReportInvokerSelectDlg() {
    report_invoker_select_dlg.dialog('open');
    report_invoker_select_controller.fresh();
}

function onReportInvokerSelected() {
    var container = $("#report_invoker_list");
    removeChildren(container);
    var rec_set = report_invoker_select_controller.get_result();
    var list_data = '';
    var employee_map = report_invoker_select_controller.employee_map;
    rec_set.forEach(function (p1, p2, p3) {
        var employee = employee_map[p1];
        list_data += '<li value="' + p1 + '">' + employee.name + ';';
        list_data += '<img class="common_small_del_btn" src="res/images/icon/gray_del.png" onclick="delReportInvoner(' + p1 + ')">';
        list_data += '</li>';
    });
    container.append(list_data);
    report_invoker_select_dlg.dialog('close');
}

function delReportInvoner(uid) {
    $("#report_invoker_list [value='" + uid + "']").remove();
    report_invoker_select_controller.remove_item(uid);
}

function queryJobList(index) {
    var param = {
        status: job_types[index]
    };
    commonPost('/api/query_job_list', param, function (data) {
        setJobData(index, data);
    });
}

function setJobData(index, data) {
    if (index < 6) {
        var weight =[1.2, 2, 1, 1.5, 1.5, 1.5];
        var title = ['类型', '主题', '发送人', '发送时间', '上一个审阅人', '最后操作时间'];
        var new_status = (index < 4 && (job_types[index] === STATUS_JOB_MARK_COMPLETED
            || job_types[index] === STATUS_JOB_INVOKED_BY_MYSELF)) || (index > 3);
        var status = {};
        if (new_status) {
            title.push('状态');
            weight.push(1);
            status[STATUS_JOB_PROCESSING] = '<span style="color: orange">处理中</span>';
            status[STATUS_JOB_COMPLETED] = '<span style="color: rgb(0,225,32)">已完成</span>';
            status[STATUS_JOB_REJECTED] = '<span style="color: red">未通过</span>';
            status[STATUS_JOB_CANCEL] = '<span style="color: gray">已撤回</span>';
        }
        var list_data = [title];
        data.forEach(function (p1, p2, p3) {
            var item = [
                '<span style="color: orange">[' + job_type_map[p1.type] + ']</span>',
                "<div class=common_clickable onclick='onClickDocItem(" + p1.type + "," + p1.id + "," + p1.branch_id + ")'>" + p1.title + "</div>",
                "<div>" + p1.invoker_name + "</div>",
                abstractDateFromDatetime(p1.time),
                commonGetString(p1.last_operator_name),
                abstractDateFromDatetime(p1.mod_time)
            ];
            if (new_status) {
                item.push(status[p1.job_status]);
            }

            list_data.push(item);
        });
        updateListView(job_list_container[index], list_data, {weight: weight});
    }
}

function onClickDocItem(job_type, job_id, branch_id) {
    switch (job_type) {
        case TYPE_JOB_OFFICIAL_DOC:
        case TYPE_JOB_DOC_REPORT:
            var url = '/doc_detail.html?job_id=' + job_id;
            if (branch_id) {
                url += '&branch_id=' + branch_id;
            }
            window.open(url, '公文详情');
            break;
        default:
            window.open('/auto_job_detail.html?job_id=' + job_id + "&title=" + encodeURI(job_type_map[job_type]), '自动化流程');
            break;
    }
}

function onQueryBtnClick() {
    var value = $("#tabs ul .ui-state-active").val();
    if (value === 4) {
        queryCompletedAutoJob();
    } else if (value === 5) {
        queryDocReport();
    } else if (value === 6) {
        exportLeaveDetail();
    }
}

function queryCompletedAutoJob() {
    var param = {query_type: TYPE_JOB_QUERY_AUTO_JOB};
    var job_type = parseInt($("#auto_job_type").val());
    if (job_type > 0) {
        param['job_type'] = job_type;
    }
    var query_content = {};
    var begin_time = $("#invoke_begin").val();
    if (begin_time) {
        query_content['begin_time'] = begin_time;
    }
    var end_time = $("#invoker_end").val();
    if (end_time) {
        query_content['end_time'] = end_time;
    }
    if (begin_time && end_time) {
        if ((new Date(end_time)).getTime() < (new Date(begin_time)).getTime()) {
            promptMsg('结束时间不能早于开始时间');
            return;
        }
    }
    var invoker_set = invoker_select_controller.get_result();
    if (invoker_set.size > 0) {
        query_content['invoker_set'] = [];
        invoker_set.forEach(function (p1, p2, p3) {
            query_content.invoker_set.push(p1);
        });
    }
    param['query_content'] = JSON.stringify(query_content);

    commonPost('/api/query_job_list', param, function (data) {
        setJobData(4, data);
    });
}

function queryDocReport() {
    var param = {query_type: TYPE_JOB_QUERY_DOC_REPORT};
    var job_type = parseInt($("#doc_type").val());
    if (job_type > 0) {
        param['job_type'] = job_type;
    }
    param['job_status'] = $("#doc_status").val();
    var query_content = {};
    var begin_time = $("#report_invoke_begin").val();
    if (begin_time) {
        query_content['begin_time'] = begin_time;
    }
    var end_time = $("#report_invoker_end").val();
    if (end_time) {
        query_content['end_time'] = end_time;
    }
    if (begin_time && end_time) {
        if ((new Date(end_time)).getTime() < (new Date(begin_time)).getTime()) {
            promptMsg('结束时间不能早于开始时间');
            return;
        }
    }
    var invoker_set = report_invoker_select_controller.get_result();
    if (invoker_set.size > 0) {
        query_content['invoker_set'] = [];
        invoker_set.forEach(function (p1, p2, p3) {
            query_content.invoker_set.push(p1);
        });
    }
    param['query_content'] = JSON.stringify(query_content);

    commonPost('/api/query_job_list', param, function (data) {
        setJobData(5, data);
    });

}

var edit_psd_dlg;
var reset_psd_list;
function decideAdminJobOperation() {
    edit_psd_dlg = $("#edit_employee_psd_dlg");
    if (__authority > __admin_authority) {
        $("#query_admin_job").hide();
        $("#admin_job_container").hide();
        edit_psd_dlg.hide();
    } else {
        commonInitDialog(edit_psd_dlg, null, {width: 680, with_ok_btn:false});
        queryAdminJob();
    }
}

function queryAdminJob() {
    var title = ['类型', '账号', '姓名', '操作'];
    var list_data = [title];
    commonPost('/api/admin_reset_psd', {op: 'query'}, function (data) {
        reset_psd_list = data;
        data.forEach(function (p1, p2, p3) {
            var id = 'div_psd_op_' + p1.id;
            list_data.push([
                '密码重置',
                '<div title="查看详细信息" class="common_clickable" onclick="openEditPsdDlg(' + p2 + ')">' + p1.account + '</div>',
                p1.name,
                '<div id="'+ id + '" style="color: green">' + getPsdOpHtml(p1, p2) + '</div>'
            ]);
        });
        updateListView($("#admin_job_container"), list_data);
    });
}

function getPsdOpHtml(data, index) {
    return data.status === STATUS_JOB_MARK_WAITING?
        '<span title="重置为初始密码：oa123456" class="common_clickable" onclick="resetToOriginalPsd(' + index + ')">重置</span>'
        : '已操作';
}

function openEditPsdDlg(index) {
    var data = reset_psd_list[index];
    var fields = ['name', 'id_card', 'cellphone'];
    fields.forEach(function (p1, p2, p3) {
        $("#" + p1 + '_from_invoker').text(data.extend[p1]);
        $("#" + p1 + '_from_sys').text(data[p1]);
        $("#" + p1 + '_compare_result').html(getCompareResult(data.extend[p1], data[p1]));
    });
    edit_psd_dlg.dialog('open');
}

function getCompareResult(a, b) {
    return a === b?
        ('<div style="color: green">相同</div>') :
        ('<div style="color: red">不相同</div>');
}

function resetToOriginalPsd(index) {
    var item = reset_psd_list[index];
    commonPost('/api/admin_reset_psd', {op: 'reset', job_id: item.id}, function (data) {
        promptMsg('重置成功');
        $("#admin_job_list").remove("[value='" + item.id + "']");
    });
}

function exportLeaveDetail() {
    var param = {};
    var leave_type = $("#leave_type").val();
    if (leave_type && leave_type !== '0') {
        param['leave_type'] = leave_type;
    }
    var dept_id = parseInt($("#leave_dept").val());
    if (dept_id && dept_id > 0) {
        param['dept_id'] = dept_id;
    }
    var min_begin_time = $("#min_begin_time").val();
    if (min_begin_time) {
        param['min_begin_time'] = min_begin_time;
    }
    var max_begin_time = $("#max_begin_time").val();
    if (max_begin_time) {
        param['max_begin_time'] = max_begin_time;
    }
    if (min_begin_time && max_begin_time) {
        if (min_begin_time >= max_begin_time) {
            promptMsg('最早开始时间应小于最迟开始时间');
            return;
        }
    }
    commonPost('/api/leave_statistics', param, function (data) {
        window.open(data);
    });
}