var job_container = [];
var job_types = [];

var invoker_select_dlg;
var invoker_select_controller;

$(document).ready(function () {
    verticalTabs();

    job_container.push(
        $("#job_waiting"),
        $("#job_processed"),
        $("#job_completed"),
        $("#job_sent_by_myself"),
        $("#job_list_container")
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

    decideQueryOperation();
});

function decideQueryOperation() {
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
        document.onkeydown = function (e) {
            if ($("#tabs ul .ui-state-active").val() === 4) {
                if (e.keyCode === 13) {
                    $("#query_btn").click();
                }
            }
        };

    } else {
        $("#query_job_tab").hide();
        $("#query_job_container").hide();
        invoker_select_dlg.hide();
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

function queryJobList(index) {
    var param = {
        status: job_types[index]
    };
    commonPost('/api/query_job_list', param, function (data) {
        setJobData(index, data);
    });
}

function setJobData(index, data) {
    if (index < 5) {
        var weight =[1.2, 2, 1, 1.5, 1.5, 1.5];
        var title = ['类型', '主题', '发送人', '发送时间', '上一个审阅人', '最后操作时间'];
        var new_status = (index < 4 && (job_types[index] === STATUS_JOB_MARK_COMPLETED
            || job_types[index] === STATUS_JOB_INVOKED_BY_MYSELF)) || index === 4;
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
        updateListView(job_container[index], list_data, {weight: weight});
    }
}

function onClickDocItem(job_type, job_id, branch_id) {
    switch (job_type) {
        case TYPE_JOB_OFFICIAL_DOC:
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

function queryAutoJob() {
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