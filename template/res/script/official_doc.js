var OP_SELECT_REC = 0;
var OP_SEND_DOC = 1;

var select_doc_rec_dlg;
var dept_list_data;
var employee_list_data;
var dept_map;
var selected_rec_dept = -1;
var selected_rec_dept_changed = false;
var selected_rec_employee = null;
var employee_map = {};

var attachment_controller = null;
var img_attachment_controller = null;


var my_doc_tabs = [];
var my_doc_tab_types = [];

$(document).ready(function () {
    verticalTabs();

    changeReceiverBtnState(false);

    $("#add_rec_btn").click(function (event) {
        openSelectRecDlg();
    });

    $("#del_rec_btn").click(function (event) {
        changeReceiverBtnState(false);
    });

    select_doc_rec_dlg = $("#select_rec_dlg");
    initDialog(select_doc_rec_dlg);
    selectMenu($("#rec_dept_selector"), function (event, ui) {
        var value = parseInt($(event.target).val());
        if (selected_rec_dept !== value) {
            selected_rec_dept = value;
            selected_rec_dept_changed = true;
            updateRecSelectable();
        }
    });
    $("#rec_type_set").buttonset();
    $("[name='radio']").on("change", function (event) {
        updateRecSelectable();
    });
    ($("#rec_single_item")).hide();
    commonSelectable($("#rec_selector"), function (selected_value) {
        selected_rec_employee = selected_value;
    });

    attachment_controller = initAttachmentController($("#attachment_container"));
    img_attachment_controller = initAttachmentController($("#img_attachment_container"), {
        type: TYPE_JOB_ATTACHMENT_IMG,
        label: '添加图片'
    });

    $("#doc_send_btn").click(function (event) {
        sendOfficialDoc();
    });

    initPromptDialog();
    initConfirmDialog();

    initDepartment();
    initMyDoc();
});

function initDialog(dialog) {
    commonInitDialog(dialog, function () {
        if (__current_operation === NULL_OPERATION) {
            dialog.dialog( "close" );
            return;
        }
        dealOperation();
    });
}

function initMyDoc() {
    $("#my_doc_tab").buttonset();
    my_doc_tabs.push($("#doc_waiting"), $("#doc_processed"), $("#doc_completed"), $("#doc_sent_by_myself"));
    my_doc_tab_types.push(STATUS_JOB_MARK_WAITING, STATUS_JOB_MARK_PROCESSED, STATUS_JOB_MARK_COMPLETED, STATUS_JOB_INVOKED_BY_MYSELF);
    showMyDocTab(0);
    my_doc_tabs.forEach(function (p1, p2, p3) {
        queryDocList(p2);
    });
    $("[name='my_doc_radio']").on('change', function (event) {
        var index = parseInt($("#my_doc_tab :radio:checked").val());
        showMyDocTab(index);
    });
}

function dealOperation() {
    switch (__current_operation) {
        case OP_SELECT_REC:
            closeSelectRecDlgWithOk();
            break;
    }
}

function onOperationResult(data) {
    try {
        if (data.status !== 0) {
            promptMsg(data.msg);
        } else {
            onOperationSuccess(data);
        }
    } catch (e) {
        redirectError(e);
    }
}

function onOperationSuccess(data) {
    switch (__current_operation) {
        case OP_SEND_DOC:
            onSendOfficialDocSuccess();
            break;
    }
}

function changeReceiverBtnState(exist_rec, receiver) {
    if (exist_rec) {
        $("#add_rec_btn").hide();
        $("#doc_rec").show();
        $("#del_rec_btn").show();
        if (receiver) {
            $("#doc_rec").text(receiver);
        }
    } else {
        $("#add_rec_btn").show();
        $("#doc_rec").hide();
        $("#del_rec_btn").hide();
    }
}

function initDepartment() {
    $.post('/api/query_dept_list', null, function (data) {
        try {
            if (data.status !== 0) {
                promptMsg(data.msg);
                return;
            }
            dept_list_data = data.data;
            dept_map = {};
            var options = '';
            dept_list_data.forEach(function (p1, p2, p3) {
                options += "<option value='" + p1.id + "'>" + p1.name + "</option>";
                dept_map[p1.id] = p1;
                if (p1.leader) {
                    employee_map[p1.leader] = {name: p1.leader_name, account: p1.leader_account};
                }
            });
            $("#rec_dept_selector").append(options).selectmenu('refresh');

        } catch(e) {
            redirectError(e);
        }
    });
}

function openSelectRecDlg() {
    select_doc_rec_dlg.dialog('open');
    __current_operation = OP_SELECT_REC;
}

function closeSelectRecDlgWithOk() {
    if (!selected_rec_employee) {
        showConfirmDialog('未选择联系人，是否关闭？', function () {
            select_doc_rec_dlg.dialog('close');
        });
    } else if (selected_rec_employee === __my_uid) {
        promptMsg('不能发送给自己');
    }else {
        changeReceiverBtnState(true, employee_map[selected_rec_employee].name);
        select_doc_rec_dlg.dialog('close');
    }
}

function updateRecSelectable() {
    if (selected_rec_dept < 0) {
        return;
    }
    selected_rec_employee = null;
    removeChildren($("#rec_selector"));
    ($("#rec_single_item")).hide();
    var type = parseInt($("#rec_type_set :radio:checked").val());
    if (type === 0) {
        if (selected_rec_dept > 0) {
            var dept = dept_map[selected_rec_dept];
            if (dept.leader) {
                $("#rec_single_item").html(getRecItem([dept.name, dept.leader_account, dept.leader_name]));
                $("#rec_single_item").show();
                selected_rec_employee = dept.leader;
            }
        }else if(selected_rec_dept === 0) {
            var list_data = '';
            dept_list_data.forEach(function (p1, p2, p3) {
                if (p1.leader) {
                    list_data += "<li value='" + p1.leader + "'>" + getRecItem([p1.name, p1.leader_account, p1.leader_name]) + "</li>";
                }
            });
            $("#rec_selector").append(list_data).selectable('refresh');
        }
    } else {
        if (!selected_rec_dept_changed && employee_list_data) {
            showEmployeeRecList();
            selected_rec_dept_changed = false;
            return;
        }
        var arg = {type: TYPE_ACCOUNT_SAMPLE};
        if (selected_rec_dept > 0) {
            arg['dept_id'] = selected_rec_dept;
        }
        $.post("/api/query_account_list", arg, function (data) {
            try {
                if (data.status !== 0) {
                    promptMsg(data.msg);
                    return;
                }
                employee_list_data = data.data;
                showEmployeeRecList();
            } catch (e) {
                redirectError(e);
            }
        });
    }
}

function showEmployeeRecList() {
    var list_data = '';
    employee_list_data.forEach(function (p1, p2, p3) {
        list_data += "<li value='" + p1.id + "'>" + getRecItem([p1.dept, p1.account, p1.name]) + "</li>";
        employee_map[p1.id] = {name: p1.name, account: p1.account};
    });
    $("#rec_selector").append(list_data).selectable('refresh');
}

function getRecItem(data) {
    var html = "";
    data.forEach(function (p1, p2, p3) {
        html += '<div class="rec_item_field">' + p1 + '</div>';
    });
    return html;
}

function sendOfficialDoc() {
    var title = $("#doc_topic").val();
    if (!title) {
        promptMsg('主题不能为空');
        return;
    }
    if (!selected_rec_employee) {
        promptMsg('请选择接收人');
        return;
    }
    var content = $("#doc_content").val();

    var param = {
        title: title,
        rec_id: selected_rec_employee,
        content: wrapJobContent(content),
        has_attachment: 0,
        has_img: 0
    };

    var attachment = attachment_controller.get_upload_files();
    if (attachment) {
        param['file_list'] = JSON.stringify(attachment);
        param['has_attachment'] = 1;
    }

    var img_attachment = img_attachment_controller.get_upload_files();
    if (img_attachment) {
        param['img_list'] = JSON.stringify(img_attachment);
        param['has_img'] = 1;
    }

    __current_operation = OP_SEND_DOC;
    $.post("/api/send_official_doc", param, onOperationResult);
}

function onSendOfficialDocSuccess() {
    promptMsg('发送成功, 2秒后自动刷新');
    setTimeout(function () {
        freshCurrent('');
    }, 2000);
}

function showMyDocTab(index) {
    my_doc_tabs.forEach(function (p1, p2, p3) {
        if (p2 === index) {
            p1.show();
        } else {
            p1.hide();
        }
    });
}

function queryDocList(index) {
    var param = {
        job_type: TYPE_JOB_OFFICIAL_DOC,
        status: my_doc_tab_types[index]
    };
    commonPost('/api/query_job_list', param, function (data) {
        setMyDocTabData(index, data);
    });
}

function setMyDocTabData(index, data) {
    var job_data = data;
    var title = ['主题', '发送人', '发送时间', '上一个审阅人', '最后操作时间'];
    var list_data = [title];
    job_data.forEach(function (p1, p2, p3) {
        list_data.push([
            "<div class=common_clickable onclick='onClickDocItem(" + p1.id + ")'>" + p1.title + "</div>",
            p1.invoker_name,
            abstractDateFromDatetime(p1.time),
            commonGetString(p1.last_operator_name),
            abstractDateFromDatetime(p1.mod_time)
        ]);
    });
    updateListView(my_doc_tabs[index], list_data, {weight: [2,1,1,1,1]});
}

function onClickDocItem(job_id) {
    window.open('/doc_detail.html?job_id=' + job_id, '公文详情');
}