var contact_type = {0: 'dept', 1: 'search'};
var TYPE_DEPT = 0;
var TYPE_SEARCH = 1;
var contact_list_data = {};
var dept_tree_data = null;
var selected_dept = null;

var level_tag_map = {0: '台领导', 1: '部门', 2: '项目组', 3: '一级小组', 4: '二级小组'};
var max_level = level_tag_map.length;
var current_deepest_level = -1;

$(document).ready(function () {
    queryDeptLevel();

    verticalTabs();

    $("#search_button").click(function (event) {
        querySearchContact();
        event.preventDefault();
    });

    selectMenu($("#condition_dept"));
    selectMenu($("#condition_status"));

    initEmployeeStatusSelector();
    initPromptDialog();

    initDept();
});

function queryDeptLevel() {
    commonPost('/api/common_config', {op: 'query', config_type: TYPE_CONFIG_DEPT_LEVEL_NAME}, function (data) {
        if (data.length === 0) {
            return;
        }
        data.forEach(function (p1, p2, p3) {
            level_tag_map[p2] = p1.label;
        });
    });
}

function initEmployeeStatusSelector() {
    var status_list = [
        [-1, '全部'],
        [STATUS_EMPLOYEE_NORMAL, '在职'],
        [STATUS_EMPLOYEE_RESIGN, '离职'],
        [STATUS_EMPLOYEE_RETIRE, '退休']
    ];
    var container = $("#condition_status");
    var options = '';
    status_list.forEach(function (p1, p2, p3) {
        if (p1[0] === STATUS_EMPLOYEE_NORMAL) {
            options += '<option selected value="' + p1[0] + '">' + p1[1] + '</option>';
        } else {
            options += '<option value="' + p1[0] + '">' + p1[1] + '</option>';
        }
    });
    container.append(options).selectmenu('refresh');
}

function initDept() {
    commonPost('/api/query_dept_list?tree=1', null, function (data) {
        dept_tree_data = data;
        addDepartment(0, 0);
    });

    commonPost('/api/query_dept_list', null, function (data) {
        var options = '';
        data.forEach(function (p1, p2, p3) {
            options += '<option value="' + p1.id + ' ">' + p1.name + '</option>';
        });
        $("#condition_dept").append(options).selectmenu('refresh');
    })
}

function queryDeptContact() {
    if (!selected_dept) {
        return;
    }
    clearContactDetail(TYPE_DEPT);
    $.post('/api/query_account_list', {type: TYPE_ACCOUNT_CONTACT, dept_id: selected_dept, status: STATUS_EMPLOYEE_NORMAL}, function (data) {
        responseContactQuery(TYPE_DEPT, data);
    });
}

function querySearchContact() {
    var conditions = {type: TYPE_ACCOUNT_CONTACT};
    var dept_id = parseInt($("#condition_dept").val());
    var has_condition = false;
    if (dept_id >= 0) {
        if (dept_id > 0) {
            conditions['dept_id'] = dept_id;
        }
        has_condition = true;
    }
    var account = $("#condition_account").val();
    if (account) {
        conditions['account'] = account;
        has_condition = true;
    }
    var name = $("#condition_name").val();
    if (name) {
        conditions['name'] = name;
        has_condition = true;
    }
    var status = parseInt($("#condition_status").val());
//    if (status !== -1) {
//        conditions['status'] = status;
//        has_condition = true;
//    }
    conditions['status'] = status
    if (!has_condition) {
        promptMsg('请输入搜索条件');
        return;
    }
    $.post('/api/query_account_list', conditions, function (data) {
        responseContactQuery(TYPE_SEARCH, data);
    });
}

function responseContactQuery(type, data) {
    try {
        if (data.status !== 0) {
            promptMsg(data.msg);
            return;
        }
        contact_list_data[type] = data.data;
        displayContactList(type, data.data,
            ['account', 'name', 'dept', 'cellphone'], ['账号', '姓名', '部门', '手机号码']);
    } catch (e) {
        redirectError(e);
    }
}

function addDepartment(parent, level) {
    if (level >= max_level) {
        promptMsg('部门级数过多，请合理规划部门结构');
        return;
    }

    clearInvalidDepartList(level);
    current_deepest_level = level;

    var data = dept_tree_data[parent].slice(1);
    if (data.length === 0) {
        return;
    }
    var dept_list_id = getDeptListId(level);
    var html = '<div id="' + dept_list_id + '_container">';
    html += (level === 0 ? '' : '<div class="common_divider"></div>');
    html += '<div class="topic_title">' + level_tag_map[level] + '</div>';
    html += '<div class="contact_dept_container">';
    html += '<ul id="' + dept_list_id + '" class="tree_list">';
    data.forEach(function (p1, p2, p3) {
        html += '<li value="' + p1.id + '">' + p1.name + '</li>';
    });
    html += '</ul></div></div>';
    $("#dept_list").append(html);
    commonSelectable($("#" + dept_list_id), onDeptSelected);
}

function clearInvalidDepartList(new_deepest_level) {
    for (var level = current_deepest_level; level >= new_deepest_level; --level) {
        $("#dept_list #" + getDeptListId(level) + "_container").remove();
    }
}

function onDeptSelected(selected_id) {
    if (selected_dept === selected_id) {
        return;
    }
    selected_dept = selected_id;
    var dept = dept_tree_data[selected_id][0];
    addDepartment(dept.id, dept.level + 1);
    queryDeptContact();
}

function getDeptListId(level) {
    return 'dept_list_level_' + level;
}

function displayContactList(type, data, fields, title) {
    var container = $("#contact_" + contact_type[type] + " ul");
    var data_list = [];
    data_list.push(title);
    data.forEach(function (element, index, array) {
        var item = [];
        fields.forEach(function (p1, p2, p3) {
            if (p2 === 0) {
                item.push(getListItemHead(element[p1], index, type));
            } else {
                item.push(element[p1]);
            }
        });
        data_list.push(item);
    });
    updateListView(container, data_list);
}

function getListItemHead(tag, index, type) {
    return '<div class="common_clickable" onclick="displayContactDetail(' + index + ',' + type +  ')">' + tag + '</div>';
}

function displayContactDetail(index, type) {
    var fields = ['account', 'name', 'dept', 'position', 'cellphone', 'email'];
    var containers = $("#contact_" + contact_type[type] + " .contact_detail_items span");
    containers.each(function (i) {
        $(this).text(contact_list_data[type][index][fields[i]]);
    })
}

function clearContactDetail(type) {
    var containers = $("#contact_" + contact_type[type] + " .contact_detail_items span");
    containers.each(function (i) {
        $(this).text('');
    });
}