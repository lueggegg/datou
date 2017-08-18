var job_type_list;
var container_prefix = 'path_container_';

var processor_selector_dlg;
var processor_selector_controller;
var insert_node = {pre_path_id: 0, next_path_id: 0};
var op = 'add';
var op_path_id;

var selected_path_type = 0;

$(document).ready(function () {
    var selector_container = $("#processor_selector_container");
    $("#path_types").buttonset();
    $("[name='path_type_radio']").on('change', function (event) {
        selected_path_type = parseInt($(event.target).val());
        if (selected_path_type === 0) {
            selector_container.hide();
        } else {
            selector_container.show();
        }
    });
    selector_container.hide();

    processor_selector_dlg = $("#processor_selector_dlg");
    commonInitDialog(processor_selector_dlg, function () {
       closeSelectorDlgWithOk();
    });

    processor_selector_controller = createTagSelectorController(selector_container, {
        type_url: '/api/query_dept_list',
        value_url: '/api/query_account_list',
        get_value_url_arg: function (tag_id) {
            return {dept_id: tag_id, type: TYPE_ACCOUNT_SAMPLE};
        },
        get_value_label: function (item) {
            return item.name + "（" + (item.is_leader? "主管": item.position) + "）";
        }
    });

    initTabs();
    initConfirmDialog();
});

function initTabs() {
    job_type_list = [
        [TYPE_JOB_CERTIFICATE_SALARY, '收入证明'],
        [TYPE_JOB_CERTIFICATE_LABOR, '在职证明'],
        [TYPE_JOB_CERTIFICATE_MARRIAGE, '婚育证明'],
        [TYPE_JOB_CERTIFICATE_INTERNSHIP, '实习证明'],
        [TYPE_JOB_HR_RESIGN, '离职申请'],
        [TYPE_JOB_HR_RECOMMEND, '伯乐推荐'],
        [TYPE_JOB_HR_ANOTHER_POST, '调岗申请'],
        [TYPE_JOB_HR_ASK_FOR_LEAVE, '请假流程'],
        [TYPE_JOB_FINANCIAL_PURCHASE, '采购流程'],
        [TYPE_JOB_FINANCIAL_REIMBURSEMENT, '报销流程']
    ];
    var tab_list_html = '';
    var tab_container_html = '';
    job_type_list.forEach(function (p1, p2, p3) {
        var id = container_prefix + p1[0];
        var text_area_id = id + '_text';
        tab_list_html += '<li value="' + p1[0] + '"><a href="#' + id + '">' + p1[1] + '</a>';
        tab_container_html += '<div id="' + id + '">';
        tab_container_html += '<div>备注信息：<span class="common_clickable" onclick="updateMemo(' + p1[0] + ')">更新</span> </div> ';
        tab_container_html += '<div><textarea id="' + text_area_id + '" class="memo_text_area"></textarea></div>';
        tab_container_html += '<button class="ui-button ui-corner-all add_path_node_btn">增加节点</button>';
        tab_container_html += '</div>';
    });
    $("#tabs ul").append(tab_list_html);
    $("#tabs").append(tab_container_html);

    verticalTabs();
    queryJobPathData();
    $(".add_path_node_btn").click(function (event) {
        op = 'add';
        insert_node.pre_path_id = 0;
        insert_node.next_path_id = 0;
        openSelectorDlg();
    });
}

function queryMemo(job_type) {
    commonPost('/api/job_memo', {op: 'query', 'job_type': job_type}, function (data) {
        if (data) {
            $("#" + container_prefix + job_type + "_text").val(abstractJobContent(data.memo));
        }
    });
}

function updateMemo(job_type) {
    var memo = $("#" + container_prefix + job_type + "_text").val();
    commonPost('/api/job_memo', {op: 'update', 'job_type': job_type, memo: wrapJobContent(memo)}, function (data) {
        promptMsg('更新备注信息成功');
    });
}

function queryJobPathData() {
    job_type_list.forEach(function (p1, p2, p3) {
        queryMemo(p1[0]);

        var container = $("#" + container_prefix + p1[0]);
        commonPost('/api/query_job_path_info', {type: p1[0]}, function (data) {
            if (data.length === 0) {
                return;
            }

            container.children('.add_path_node_btn').hide();
            var path_node_map = {};
            var head = null;
            data.forEach(function (item, index, arr) {
                path_node_map[item.id] = item;
                if (!item.pre_path_id) {
                    head = item.id;
                }
            });
            while (head) {
                var node = path_node_map[head];
                createJobPathNode(container, node);
                head = node.next_path_id;
            }
        });

    });
}

function createJobPathNode(container, node_data) {
    var html = '<div class="job_path_node_container" id="job_path_node_container_' + node_data.id + '">';

    html += '<div class="job_path_node_list_container"><ul>';
    if (node_data.to_leader) {
        html += '<li class="leader_item">直属主管</li>';
    } else {
        var dept_list = '';
        var uid_list = '';
        var divider = '　　';
        node_data.detail.forEach(function (p1, p2, p3) {
            if (p1.dept_id) {
                dept_list += '<li class="dept_item">' + p1.dept + '（全员）</li>';
            } else if (p1.uid) {
                uid_list += '<li class="employee_item">' + p1.uid_dept + divider + p1.account + divider + p1.employee + '</li>';
            }
        });
        html += dept_list + uid_list;
    }
    html += '</ul></div>';

    html += '<div class="job_path_node_op_container">';
    html += '<div><img title="删除" onclick="delPathNode(' + node_data.id + ')" src="/res/images/icon/red_del.png" class="common_small_del_btn"></div>';
    html += '<div><span onclick="insertPathNode(' + getDirectionId(node_data.pre_path_id) + ',' + node_data.id + ')" class="common_clickable">在前面插入节点</span></div>';
    html += '<div><span onclick="insertPathNode(' + node_data.id + ',' + getDirectionId(node_data.next_path_id) + ')" class="common_clickable">在后面插入节点</span></div>';
    html += '<div><span onclick="resetPathNode(' + node_data.id + ')" class="common_clickable">重置该节点</span></div>';
    html += '</div>';

    html += '</div>';
    container.append(html);
}

function getDirectionId(dir_id) {
    return dir_id? dir_id : 0;
}

function delPathNode(path_id) {
    showConfirmDialog('确认删除该节点？', function () {
        commonPost('/api/alter_job_path', {job_type: getSelectedJob(), path_id: path_id, op: 'del'}, function (data) {
            refresh();
        })
    });
}

function insertPathNode(pre_path_id, next_path_id) {
    op = 'add';
    insert_node.pre_path_id = pre_path_id;
    insert_node.next_path_id = next_path_id;
    openSelectorDlg();
}

function resetPathNode(path_id) {
    op = 'update';
    op_path_id = path_id;
    openSelectorDlg();
}

function getSelectedJob() {
    return $("#tabs ul .ui-state-active").val();
}

function openSelectorDlg() {
    processor_selector_dlg.dialog('open');
}

function closeSelectorDlgWithOk() {
    var param = {
        op: op,
        job_type: getSelectedJob()
    };
    if (selected_path_type === 0) {
        param['to_leader'] = 1;
        param['path_id'] = op_path_id;
    } else {
        if (op === 'add') {
            if (insert_node.pre_path_id) {
                param['pre_path_id'] = insert_node.pre_path_id;
            }
            if (insert_node.next_path_id) {
                param['next_path_id'] = insert_node.next_path_id;
            }
        } else if (op === 'update') {
            param['path_id'] = op_path_id;
        } else {
            promptMsg('系统错误: wrong op type while close dlg');
            return;
        }

        var result = processor_selector_controller.get_result();
        switch (result.status) {
            case 0:
                promptMsg('请选择审批部门或者审批员工');
                return;
            case 1:
                param['dept_list'] = JSON.stringify(result.type_list);
                break;
            case 2:
                param['uid_list'] = JSON.stringify(result.value_list);
                break;
            case 3:
                param['dept_list'] = JSON.stringify(result.type_list);
                param['uid_list'] = JSON.stringify(result.value_list);
                break;
        }
    }

    commonPost('/api/alter_job_path', param, function (data) {
       processor_selector_dlg.dialog('close');
       refresh();
    });
}

function refresh() {
    freshCurrent(container_prefix + getSelectedJob());
}