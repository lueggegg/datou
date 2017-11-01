var OP_SELECT_REC = 0;
var OP_SEND_DOC = 1;

var select_doc_rec_dlg;

var attachment_controller = null;
var img_attachment_controller = null;


var my_doc_tabs = [];
var my_doc_tab_types = [];

var rec_selectable_controller;

var item_per_page = 15;
var page_controllers = [];
var my_doc_detail_containers = [];

$(document).ready(function () {
    verticalTabs();

    $("#add_rec_btn").click(function (event) {
        openSelectRecDlg();
    });

    select_doc_rec_dlg = $("#select_rec_dlg");
    commonInitDialog(select_doc_rec_dlg, onSelectedRec, {width: 720});
    rec_selectable_controller = createEmployeeMultiSelectorController($("#employee_selectable_container"), {filter_list: [__my_uid]});

    attachment_controller = initAttachmentController($("#attachment_container"));
    img_attachment_controller = initAttachmentController($("#img_attachment_container"), {
        type: TYPE_JOB_ATTACHMENT_IMG,
        label: '添加图片'
    });

    $("#doc_send_btn").click(function (event) {
        sendOfficialDoc();
    });

    initCommonWaitingDialog();
    initConfirmDialog();

    initMyDoc();
});

function initMyDoc() {
    $("#my_doc_tab").buttonset();
    my_doc_tabs.push($("#doc_waiting"), $("#doc_processed"), $("#doc_completed"), $("#doc_sent_by_myself"));
    my_doc_tab_types.push(STATUS_JOB_MARK_WAITING, STATUS_JOB_MARK_PROCESSED, STATUS_JOB_MARK_COMPLETED, STATUS_JOB_INVOKED_BY_MYSELF);
    showMyDocTab(0);
    my_doc_tabs.forEach(function (p1, p2, p3) {
        p1.append('<div></div><div></div>');
        var c = p1.children();
        my_doc_detail_containers.push([$(c[0]), $(c[1])]);
        initDocList(p2);
    });
    $("[name='my_doc_radio']").on('change', function (event) {
        var index = parseInt($("#my_doc_tab :radio:checked").val());
        showMyDocTab(index);
    });
}

function onSelectedRec() {
    var container = $("#rec_list");
    removeChildren(container);
    var rec_set = rec_selectable_controller.get_result();
    var list_data = '';
    var employee_map = rec_selectable_controller.employee_map;
    rec_set.forEach(function (p1, p2, p3) {
        var employee = employee_map[p1];
        list_data += '<li value="' + p1 + '">' + employee.name + ';';
        list_data += '<img class="common_small_del_btn" src="res/images/icon/gray_del.png" onclick="delRec(' + p1 + ')">';
        list_data += '</li>';
    });
    container.append(list_data);
    select_doc_rec_dlg.dialog('close');
}

function delRec(uid) {
    $("#rec_list [value='" + uid + "']").remove();
    rec_selectable_controller.remove_item(uid);
}

function openSelectRecDlg() {
    select_doc_rec_dlg.dialog('open');
    __current_operation = OP_SELECT_REC;
    rec_selectable_controller.fresh();
}

function sendOfficialDoc() {
    var title = $("#doc_topic").val();
    if (!title) {
        promptMsg('主题不能为空');
        return;
    }
    var rec_set = rec_selectable_controller.get_result();
    if (rec_set.size === 0) {
        promptMsg('请选择接收人');
        return;
    }
    var content = $("#doc_content").val();

    var rec_list = [];
    rec_set.forEach(function (p1, p2, p3) {
       rec_list.push(p1);
    });
    var param = {
        op: 'add',
        title: title,
        content: wrapJobContent(content),
        has_attachment: 0,
        has_img: 0,
        rec_set: JSON.stringify(rec_list),
        sub_type: $("#branch_type").is(':checked')? TYPE_JOB_OFFICIAL_DOC_BRANCH : TYPE_JOB_OFFICIAL_DOC_GROUP
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
    commonPost("/api/send_official_doc", param, function (data) {
        promptMsg('发送成功, 2秒后自动刷新');
        setTimeout(function () {
            freshCurrent('');
        }, 2000);
    }, true);
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

function initDocList(index) {
    page_controllers[index] = createPageController(my_doc_detail_containers[index][1], item_per_page, queryDocList, index);
    queryDocList(0, item_per_page, index);
}

function queryDocList(offset, count, index) {
    var param = {
        job_type: TYPE_JOB_OFFICIAL_DOC,
        status: my_doc_tab_types[index],
        offset: offset,
        count: count
    };
    commonPost('/api/query_job_list', param, function (data, ori_data) {
        setMyDocTabData(index, data);
        page_controllers[index].updateTotalCount(ori_data.total);
    });
}

function setMyDocTabData(index, data) {
    var job_data = data;
    var title = ['主题', '发送人', '发送时间', '上一回复', '最后操作时间'];
    var list_data = [title];
    job_data.forEach(function (p1, p2, p3) {
        list_data.push([
            "<div class=common_clickable  title='" + p1.title + "' onclick='onClickDocItem(" + p1.id + "," + p1.branch_id + ")'>" + p1.title + "</div>",
            p1.invoker_name,
            abstractDateFromDatetime(p1.time),
            commonGetString(p1.last_operator_name),
            abstractDateFromDatetime(p1.mod_time)
        ]);
    });
    updateListView(my_doc_detail_containers[index][0], list_data, {weight: [2,1,1,1,1]});
}

function onClickDocItem(job_id, branch_id) {
    var url = '/doc_detail.html?job_id=' + job_id;
    if (branch_id) {
        url += '&branch_id=' + branch_id;
    }
    window.open(url, '公文详情');
}