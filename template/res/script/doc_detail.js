var OP_SELECT_REC = 0;
var OP_SEND_DOC = 1;

var query_url = '/api/query_job_info';
var attachment_controller = null;
var img_attachment_controller = null;
var doc_type_name = '公文';

var process_container_init = false;

var select_doc_rec_dlg;
var dept_list_data;
var employee_list_data;
var dept_map;
var selected_rec_dept = -1;
var selected_rec_dept_changed = false;
var selected_rec_employee = null;
var employee_map = {};

var main_info = null;
var first_node = null;
var node_list_data_map = {};
var current_branch;
var current_branch_container;
var active_branch_tag;

var rec_selectable_controller;

var custom_content = false;
var add_new_member = false;
var has_attachment = false;
var has_img_attachment = false;
var state_quick_reply = true;

$(document).ready(function (event) {

    if (!isAuthorized(OPERATION_MASK_QUERY_REPORT)) {
        checkAuthority();
    }

    if (__notify) {
        commonPost('/api/alter_job', {job_id: __job_id, op: 'notify_read'}, function (data) {
        });
    }

    $("#process_container").hide();
    
    queryJobBaseInfo();

    select_doc_rec_dlg = $("#select_rec_dlg");

    var reply_input = $("#doc_content");
    reply_input.val('');
    reply_input.on('input', function () {
        custom_content = !!$.trim(reply_input.val());
        setSendButtonState();
    });

    initConfirmDialog();
    current_branch = __branch_id;
});

function setSendButtonState() {
    state_quick_reply = !(custom_content || has_attachment || add_new_member || has_img_attachment);
    $("#doc_send_btn").text(state_quick_reply? '已阅' : '回复');
}

function checkAuthority() {
    commonPost('/api/query_job_info', {type: 'authority', job_id: __job_id, branch_id: __branch_id}, function (data) {
        if (!data) {
            redirectError('没有权限');
        }
    });
}

function initBranchProcessContainer() {
    if (process_container_init) return;

    changeReceiverBtnState(false);

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
        var last_node = getLastNode();
        selected_rec_employee = last_node.sender_id;
        changeReceiverBtnState(true, last_node.sender);
    });

    $("#reply_invoker_btn").click(function (event) {
        selected_rec_employee = main_info.invoker;
        changeReceiverBtnState(true, main_info.invoker_name);
    });

    initCommonProcessContainer();

    initDepartment();
}

function initCommonProcessContainer() {
    $("#add_rec_btn").click(function (event) {
        openSelectRecDlg();
    });
    attachment_controller = initAttachmentController($("#attachment_container"), {
        change: function () {
            has_attachment = !!attachment_controller.get_upload_files();
            setSendButtonState();
        }
    });
    img_attachment_controller = initAttachmentController($("#img_attachment_container"), {
        type: TYPE_JOB_ATTACHMENT_IMG,
        label: '添加图片',
        change: function () {
            has_img_attachment = !!img_attachment_controller.get_upload_files();
            setSendButtonState();
        }
    });

    $("#doc_send_btn").click(function (event) {
        replyDoc();
    });
}

function initDialog(dialog) {
    commonInitDialog(dialog, function () {
        if (__current_operation === NULL_OPERATION) {
            dialog.dialog( "close" );
            return;
        }
        dealOperation();
    }, {width: 720});
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
    if (rec_selectable_controller) {
        rec_selectable_controller.fresh();
    }
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
        if (main_info.type === TYPE_JOB_DOC_REPORT) {
            doc_type_name = '呈报表';
            $('title').text(doc_type_name + '详情');
        }
        $("#doc_topic").text(main_info.title);
        $("#doc_topic").attr('title', main_info.title);
        if (main_info.status === STATUS_JOB_COMPLETED) {
            $("#complete_btn").remove();
            $("#cancel_btn").remove();
            $("#job_status").text("已归档");
            initExport();
        } else if (main_info.status === STATUS_JOB_CANCEL || main_info.status === STATUS_JOB_SYS_CANCEL) {
            $("#complete_btn").remove();
            $("#cancel_btn").remove();
            $("#export_btn").remove();
            $("#job_status").text(main_info.status === STATUS_JOB_CANCEL?"已撤回" : '系统撤回');
        }else {
            $("#export_btn").remove();
            $("#job_status").text("处理中");
            if (!isAuthorized(OPERATION_MASK_QUERY_REPORT) && main_info.invoker !== __my_uid) {
                $("#complete_btn").remove();
                $("#cancel_btn").remove();
            } else {
                $("#complete_btn").click(function (event) {
                    showConfirmDialog('归档后，不能再操作该' + doc_type_name + '。确认归档？', function () {
                        var param = {job_id: main_info.id};
                        commonPost('/api/alter_job', param, function (data) {
                            refresh();
                        });
                    });
                });
                if (main_info.invoker === __my_uid) {
                    $("#cancel_btn").click(function (event) {
                        showConfirmDialog('撤回该' + doc_type_name + '？', function () {
                            commonPost('/api/alter_job', {op: 'cancel', job_id: __job_id}, function (data) {
                                promptMsg('撤消成功，2s后自动刷新...');
                                setTimeout(function () {
                                    refresh();
                                }, 2000);
                            });
                        });
                    });
                } else {
                    $("#cancel_btn").remove();
                }
            }
            if (main_info.sub_type === TYPE_JOB_SUB_TYPE_GROUP) {
                commonPost('/api/alter_job', {op: 'group_doc_read', job_id: __job_id}, null);
            }
        }
        queryFirstJobNode();
    });
}

function initExport() {
    $("#export_btn").click(function () {
        commonPost('/api/job_export', {op: 'single', job_id: __job_id}, function (data) {
            window.open(data);
        });
    });
}

function onBranchChange(branch_id) {
    var branch_container = $("#branch_container_" + branch_id);
    current_branch = branch_id;
    if (current_branch_container !== branch_container) {
        if (current_branch_container) {
            current_branch_container.hide();
            active_branch_tag.removeClass('branch_tag_active');
        }
        current_branch_container = branch_container;
        current_branch_container.show();
        active_branch_tag = $("#branch_tag_container ul [value='" + branch_id + "']");
        if (active_branch_tag) {
            active_branch_tag.addClass('branch_tag_active');
        }

        var last_node = getLastNode();
        if (last_node.rec_id === __my_uid) {
            $("#process_container").show();
        } else {
            $("#process_container").hide();
        }
    }
}

function queryFirstJobNode() {
    commonPost(query_url, {type: 'node', job_id: __job_id, count: 1}, function (data) {
        var node_data = data[0];
        first_node = node_data;
        addJobNodeItem($("#first_node_container"), node_data, 0, false);
        if (main_info.sub_type === TYPE_JOB_SUB_TYPE_GROUP) {
            initGroupDoc();
        } else {
            initBranchDoc();
        }
    });
}

function initGroupDoc() {
    $("#rec_container").remove();
    $("#sp_rec_picker_container").remove();
    var rec_container = '<div class="rec_container"><ul id="rec_list"></ul>';
    rec_container += '<button id="add_rec_btn" class="node_info_item_add_btn" title="添加新的员工（可不添加）"></button></div>';
    $("#node_info_item").append(rec_container);

    var container = $("#branch_tag_container");
    commonPost(query_url, {type: 'rec_set', set_id: first_node.rec_set, job_id: __job_id}, function (data) {
        var html = '<ul>';
        var filter_list = [main_info.invoker];
        data.forEach(function (p1, p2, p3) {
            html += '<li>' + p1.name + '</li>';
            filter_list.push(p1.uid);
        });
        html += '</ul>';
        container.append(html);

        commonInitDialog(select_doc_rec_dlg, onSelectedMultiRec, {width: 720});
        if (main_info.status !== STATUS_JOB_COMPLETED && main_info.status !== STATUS_JOB_CANCEL) {
            removeChildren(select_doc_rec_dlg);
            select_doc_rec_dlg.append('<div id="employee_selectable_container"></div>');
            rec_selectable_controller = createEmployeeMultiSelectorController($("#employee_selectable_container"), {filter_list: filter_list});

            initCommonProcessContainer();

            $("#process_container").show();
        }
    });
    queryAllJobNode();
}

function onSelectedMultiRec() {
    var container = $("#rec_list");
    removeChildren(container);
    var rec_set = rec_selectable_controller.get_result();
    var list_data = '';
    var employee_map = rec_selectable_controller.employee_map;
    rec_set.forEach(function (p1, p2, p3) {
        var employee = employee_map[p1];
        list_data += '<li value="' + p1 + '">' + employee.name + ';';
        list_data += '<img class="common_small_del_btn" src="res/images/icon/gray_del.png" onclick="delRecFromMulti(' + p1 + ')">';
        list_data += '</li>';
    });
    container.append(list_data);
    select_doc_rec_dlg.dialog('close');
    onRecChange();
}

function delRecFromMulti(uid) {
    $("#rec_list [value='" + uid + "']").remove();
    rec_selectable_controller.remove_item(uid);
    onRecChange();
}

function onRecChange() {
    add_new_member = rec_selectable_controller.get_result().size > 0;
    setSendButtonState();
}

function initBranchDoc() {
    initDialog(select_doc_rec_dlg);

    if (!first_node.rec_id) {
        first_node.rec_id = __branch_id;
    }
    var container = $("#branch_tag_container");
    if (first_node.sender_id === __my_uid ) {
        commonPost(query_url, {type: 'rec_set', set_id: first_node.rec_set, job_id: __job_id}, function (data) {
            var html = '<ul>';
            data.forEach(function (p1, p2, p3) {
                html += '<li value="' + p1.uid + '" onclick="onBranchChange(' + p1.uid + ')">' + p1.name + '</li>';
                queryJobNodeBranchList(p1);
            });
            html += '</ul>';
            container.append(html);
        });
    } else {
        container.hide();
        queryJobNodeBranchList({uid: __branch_id, account:'', name: '', dept: ''});
    }
}

function queryAllJobNode() {
    commonPost(query_url, {type: 'node', job_id: __job_id}, function (data) {
        data.shift();
        var container = $("#doc_branch_node_container");
        data.forEach(function (p1, p2, p3) {
           addJobNodeItem(container, p1, p2+1);
        });
    });
}

function queryJobNodeBranchList(branch) {
    var branch_id = branch.uid;
    commonPost(query_url, {type: 'node', job_id: __job_id, branch_id: branch_id}, function(data) {
        node_list_data_map[branch_id] = data;
        var last_node = null;
        $("#doc_branch_node_container").append('<div id="branch_container_' + branch_id + '"></div>');
        var branch_container = $("#branch_container_" + branch_id);
        if (current_branch === branch_id) {
            onBranchChange(branch_id);
        } else {
            branch_container.hide();
        }
        data.forEach(function (p1, p2, p3) {
            addJobNodeItem(branch_container, p1, p2 + 1);
            last_node = p1;
        });
        if (main_info.status === STATUS_JOB_COMPLETED) {
            $("#process_container").hide();
        } else {
            if (!last_node) {
                last_node = {rec_account: branch.account, rec_name: branch.name, rec_dept: branch.dept, rec_id: branch.uid};
            }
            if (last_node.rec_id !== __my_uid) {
                // $("#process_container").hide();

                var fake_node = {
                    account: last_node.rec_account,
                    sender: last_node.rec_name,
                    dept: last_node.rec_dept,
                    time: '',
                    content: '{【处理中...】}',
                    type: 'fake',
                    id: 'fake_' + (new Date()).getTime()
                };
                addJobNodeItem(branch_container, fake_node, -1, true);
            } else {
                initBranchProcessContainer();
            }
        }
    });
}

function getLastNode() {
    if (!current_branch) {
        return first_node;
    } else {
        var list_data = node_list_data_map[current_branch];
        if (list_data.length === 0) {
            return first_node;
        } else {
            return list_data[list_data.length - 1];
        }
    }
}

function addJobNodeItem(container, node_data, index, fake) {
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
    if (node_data.type === TYPE_JOB_NODE_REMIND_COMPLETE) {
        html += "<div class='sp_type_info'>【审阅者提醒：归档该" + doc_type_name + "】</div>";
    }
    html += "<div class='node_item_content' id='node_item_content_" + node_data.id + "'></div>";
    html += "</div>";
    container.append(html);
    var content_html = '';
    if (node_data.hasOwnProperty('extend') && node_data.extend) {
        content_html += '<div class="node_extend_container">' + parseJobContent(node_data.extend) + '</div>';
    }
    var img_list_html = '';
    if (node_data.has_img) {
        img_list_html += "<ul>";
        node_data.img_attachment.forEach(function (p1, p2, p3) {
           img_list_html += "<li><img src='" + p1.path + "'></li>";
        });
        img_list_html += "</ul>";
    }
    content_html += img_list_html + parseJobContent(node_data.content);
    $("#node_item_content_" + node_data.id).html(content_html);
}

function replyDoc() {
    var param = {
        has_attachment: 0,
        has_img: 0,
        op: 'reply',
        job_id: __job_id
    };

    if (rec_selectable_controller) {
        var rec_set = rec_selectable_controller.get_result();
        var rec_list = [];
        rec_set.forEach(function (p1, p2, p3) {
            rec_list.push(p1);
        });
        param['rec_set'] = JSON.stringify(rec_list);
    } else {
        if (!selected_rec_employee) {
            promptMsg('请选择接收人');
            return;
        }
        param['rec_id'] = selected_rec_employee;
        param['branch_id'] = current_branch;

        if ($("#request_to_complete").is(":checked")) {
            param['node_type'] = TYPE_JOB_NODE_REMIND_COMPLETE;
        }
    }

    var content = $("#doc_content").val();
    if (custom_content && !has_img_attachment && !has_attachment && !add_new_member) {
        var filter = ['已阅', '收到'];
        if ($.inArray(content, filter) !== -1) {
            state_quick_reply = true;
        }
    }
    if (state_quick_reply) {
        param['quick_reply'] = 1;
        if (!custom_content) {
            content = '已阅';
        }
    }
    param['content'] = wrapJobContent(content);

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
    window.location.reload();
}