var OP_SELECT_REC = 0;
var OP_SEND_DOC = 1;

var query_url = '/api/query_job_info';
var attachment_controller = null;
var img_attachment_controller = null;

var select_doc_rec_dlg;
var dept_list_data;
var employee_list_data;
var dept_map;
var selected_rec_dept = -1;
var selected_rec_dept_changed = false;
var selected_rec_employee = null;
var employee_map = {};

var main_info = null;
var node_list_data = null;

$(document).ready(function (event) {
    queryJobBaseInfo();

    select_doc_rec_dlg = $("#select_rec_dlg");
    initDialog(select_doc_rec_dlg);

    initConfirmDialog();
});

function initProcessContainer() {
    changeReceiverBtnState(false);

    $("#add_rec_btn").click(function (event) {
        openSelectRecDlg();
    });

    $("#del_rec_btn").click(function (event) {
        changeReceiverBtnState(false);
    });

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
    $('#reply_last_btn').click(function (event) {
        var last_node = node_list_data[node_list_data.length - 1];
        selected_rec_employee = last_node.sender_id;
        changeReceiverBtnState(true, last_node.sender);
    });

    $("#reply_invoker_btn").click(function (event) {
        selected_rec_employee = main_info.invoker;
        changeReceiverBtnState(true, main_info.invoker_name);
    });

    attachment_controller = initAttachmentController($("#attachment_container"));
    img_attachment_controller = initAttachmentController($("#img_attachment_container"), {
        type: TYPE_JOB_ATTACHMENT_IMG,
        label: '添加图片'
    });

    $("#doc_send_btn").click(function (event) {
        replyDoc();
    });

    initDepartment();
}

function initDialog(dialog) {
    commonInitDialog(dialog, function () {
        if (__current_operation === NULL_OPERATION) {
            dialog.dialog( "close" );
            return;
        }
        dealOperation();
    });
}

function initDepartment() {
    commonPost('/api/query_dept_list', null, function (data) {
        dept_list_data = data;
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
    });
}

function changeReceiverBtnState(exist_rec, receiver) {
    if (exist_rec) {
        $("#add_rec_btn").hide();
        $("#doc_rec").show();
        $("#del_rec_btn").show();
        if (receiver) {
            $("#doc_rec").text(receiver);
        }
        $(".quick_rec_selector").hide();
        if (selected_rec_employee === main_info.invoker) {
            $(".remind_complete_container").show();
        } else {
            $(".remind_complete_container").hide();
        }
    } else {
        $("#add_rec_btn").show();
        $("#doc_rec").hide();
        $("#del_rec_btn").hide();
        $(".quick_rec_selector").show();
        $(".remind_complete_container").hide();
    }
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

function queryJobBaseInfo() {
    commonPost(query_url, {type: 'base', job_id: __job_id}, function (data) {
        main_info = data;
        $("#doc_topic").text(main_info.title);
        $("#doc_topic").attr('title', main_info.title);
        if (main_info.status === STATUS_JOB_COMPLETED) {
            $("#complete_btn").remove();
            $("#job_status").text("已归档");
        } else {
            $("#job_status").text("处理中");
            if (main_info.invoker !== __my_uid) {
                $("#complete_btn").remove();
            } else {
                $("#complete_btn").click(function (event) {
                    showConfirmDialog('归档后，不能再操作该公文。确认归档？', function () {
                        commonPost('/api/alter_job', {job_id: main_info.id}, function (data) {
                            refresh();
                        });
                    });
                });
            }
        }
        queryJobNodeList();
    });
}

function queryJobNodeList() {
    commonPost(query_url, {type: 'node', job_id: __job_id}, function(data) {
        node_list_data = data;
        var last_node;
        data.forEach(function (p1, p2, p3) {
            addJobNodeItem(p1, p2);
            last_node = p1;
        });
        if (main_info.status === STATUS_JOB_COMPLETED) {
            $("#process_container").hide();
        } else {
            if (last_node.rec_id !== __my_uid) {
                $("#process_container").hide();

                var fake_node = {
                    account: last_node.rec_account,
                    sender: last_node.rec_name,
                    dept: last_node.rec_dept,
                    time: '',
                    content: '【处理中...】'
                };
                addJobNodeItem(fake_node, -1, true);
            } else {
                initProcessContainer();
            }
        }
    });
}

function addJobNodeItem(node_data, index, fake) {
    fake = !!fake;
    var html = "<div class='node_item_container'>";
    if (fake) {
        html += "<div class='fake_node_item_header'>";
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
    html += getListViewHtml(header_data, {weight: [1, 1, 1, 2], without_title: true, diff_background: false, ul_class: 'node_item_header_ul'});
    html += "</div>";
    if (node_data.has_attachment) {
        html += "<div class='node_item_attachment'>附件：";
        html += "<ul>";
        node_data.attachment.forEach(function (p1, p2, p3) {
           html += "<li><a target='_blank' href='" + p1.path + "'>" + p1.name + "</a></li>";
        });
        html += "</ul></div>";
    }
    if (node_data.type === TYPE_JOB_NODE_REMIND_COMPLETE) {
        html += "<div class='sp_type_info'>【审阅者提醒：归档该公文】</div>";
    }
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
    $("#node_item_content_" + node_data.id).html(img_list_html + html2Text(abstractJobContent(node_data.content)));
}

function replyDoc() {
    if (!selected_rec_employee) {
        promptMsg('请选择接收人');
        return;
    }
    var content = $("#doc_content").val();

    var param = {
        rec_id: selected_rec_employee,
        content: wrapJobContent(content),
        has_attachment: 0,
        has_img: 0,
        op_type: 'reply',
        job_id: __job_id
    };

    if ($("#request_to_complete").is(":checked")) {
        param['node_type'] = TYPE_JOB_NODE_REMIND_COMPLETE;
    }

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
    commonPost("/api/send_official_doc", param, function (data) {
        promptMsg('发送成功, 2秒后自动刷新');
        setTimeout(function () {
            refresh();
        }, 2000);
    });
}

function dealOperation() {
    switch (__current_operation) {
        case OP_SELECT_REC:
            closeSelectRecDlgWithOk();
            break;
    }
}

function refresh() {
    window.location.href = '/doc_detail.html?job_id=' + __job_id;
}