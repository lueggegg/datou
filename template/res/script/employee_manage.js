var dept_dialog = null;
var operate_dept = null;
var selected_dept_for_employee = null;
var operate_employee = null;
var operate_employee_authority = 1024;
var department_list_data = null;
var employee_list_data = null;
var operate_reset_employee_password = false;
var departments_map = null;
var join_date = null;
var birthday = null;

var EDIT_DEPT = 0;
var DEL_DEPT = 1;
var ADD_DEPT = 2;
var EDIT_EMPLOYEE = 10;
var DEL_EMPLOYEE = 11;
var ADD_EMPLOYEE = 12;
var SET_EMPLOYEE_WEIGHT = 13;
var RESET_EMPLOYEE_PSD = 14;
var SET_DEPT_LEADER = 20;
var current_operation = NULL_OPERATION;

var dept_leader_setting_dlg;
var employee_weight_dlg;
var employee_psd_dlg;

$(document).ready(function () {
    needAuthority(OPERATION_MASK_EMPLOYEE);

    verticalTabs("#tabs");

    dept_dialog = $( "#edit_dept_dialog" );
    dept_leader_setting_dlg = $("#edit_dept_leader_dlg");
    employee_weight_dlg = $("#edit_employee_weight_dlg");
    employee_psd_dlg = $("#edit_employee_psd_dlg");

    initDialog(dept_dialog);
    initDialog(dept_leader_setting_dlg);
    initDialog(employee_weight_dlg);
    initDialog(employee_psd_dlg);

    $( "#add_dept" ).click(function( event ) {
        current_operation = ADD_DEPT;
        openDeptDialog('增加部门', '', 'null');
    });

    $( "#add_employee" ).click(function( event ) {
        window.open('employee_info_table.html?op=add');
    });


    selectMenu($("#current_department_menu"));
    selectMenu($("#leader_dept"));
    selectMenu($("#dept_leader_selector"));
    selectMenu($("#statistics_dept"));
    selectMenu($("#statistics_type"));

    $.post('/api/query_dept_list', null, setDepartmentList) ;

    initConfirmDialog();
});

function initPageWhileHasCondition() {
    if (__dept_id) {
        $("#current_department_menu").val(__dept_id).selectmenu('refresh');
        queryDepartmentEmployees(__dept_id);
    }
}

function initDialog(dialog, width) {
    if (!width) {
        width = 400;
    }
    dialog.dialog({
        autoOpen: false,
        modal: true,
        width: width,
        buttons: [
            {
                text: "确定",
                click: function() {
                    if (current_operation === NULL_OPERATION) {
                        $( this ).dialog( "close" );
                        return;
                    }
                    dealOperation();
                }
            },
            {
                text: "取消",
                click: function() {
                    current_operation = NULL_OPERATION;
                    $( this ).dialog( "close" );
                }
            }
        ]
    });
}

function dealOperation() {
    switch (current_operation) {
        case EDIT_DEPT:
            updateDepartment();
            break;
        case ADD_DEPT:
            addDepartment();
            break;
        case DEL_DEPT:
            deleteDepartment();
            break;
        case DEL_EMPLOYEE:
            deleteEmployee();
            break;
        case SET_DEPT_LEADER:
            var uid = $("#dept_leader_selector").val();
            if (!uid || uid === '-1') {
                promptMsg('请选择员工');
                return;
            }
            setDeptLeader(selected_dept, uid, $("#relative_report_uid_checkbox").is(':checked'));
            break;
        case SET_EMPLOYEE_WEIGHT:
            setEmployeeWeight();
            break;
        case RESET_EMPLOYEE_PSD:
            resetEmployeePsd();
            break;
    }
}

function openEmployeeWeightDlg(data) {
    $("#employee_weight").val(data.weight);
    operate_employee = data.id;
    employee_weight_dlg.dialog('open');
}

function openEmployeePsdDlg() {
    $("#new_psd").val('');
    $("#confirm_psd").val('');
    employee_psd_dlg.dialog('open');
}

function setEmployeeWeight() {
    var weight = $("#employee_weight").val();
    if (!weight || isNaN(weight)) {
        promptMsg('请输入正确的权重');
        return;
    }
    commonPost('/api/alter_account',
        {uid: operate_employee, account_info: JSON.stringify({weight: weight}), op: 'update'}, function (data) {
            freshCurrent('employee_config_container');
        });
}

function resetEmployeePsd() {
    var new_psd = $("#new_psd").val();
    if (!new_psd) {
        promptMsg('请输入新密码');
        return;
    }
    var confirm_psd = $("#confirm_psd").val();
    if (!confirm_psd) {
        promptMsg('请确认密码');
        return;
    }
    if (new_psd !== confirm_psd) {
        promptMsg('请输入相同的密码');
        return;
    }
    commonPost('/api/alter_account',
        {uid: operate_employee, account_info: JSON.stringify({password: getHash(new_psd)}), op: 'update'}, function (data) {
            freshCurrent('employee_config_container');
        });
}

function openLeaderSettingDlg(dept_id) {
    commonPost('/api/query_account_list', {dept_id: dept_id}, function (data) {
        var container = $("#dept_leader_selector");
        removeChildren(container);
        var options = '<option selected disabled value="-1">请选择</option>';
        data.forEach(function (p1, p2, p3) {
            options += '<option value="' + p1.id + '">' + p1.name + '</option>';
        });
        container.append(options).selectmenu('refresh');
        dept_leader_setting_dlg.dialog('open');
        selected_dept = dept_id;
        current_operation = SET_DEPT_LEADER;
    });
}

function updateDepartment() {
    var dept_name = $("#dept_name").val();
    if (!dept_name) {
        promptMsg('部门名称不能为空');
        return;
    }
    var leader_dept = $("#leader_dept").val();
    if (leader_dept === 'null') {
        if (__authority > __admin_authority) {
            promptMsg('权限不足（非管理员不能设置上级部门为空）');
            return;
        }
        leader_dept = null;
    } else {
        leader_dept = parseInt(leader_dept);
    }
    if (leader_dept === operate_dept) {
        promptMsg('不能将自身作为上级部门');
        return;
    }
    var weight = $("#dept_weight").val();
    if (!weight) {
        promptMsg('请输入权重');
        return;
    }
    if (isNaN(weight)) {
        promptMsg('权重请输入数字');
        return;
    }
    var data = {name: dept_name, parent: leader_dept, weight: weight};
    data = JSON.stringify(data);
    $.post( '/api/alter_dept', {dept_info: data, dept_id: operate_dept, op: 'update'}, operationResult);
}

function deleteDepartment() {
    $.post('/api/alter_dept', {dept_id: operate_dept, op: 'del'}, operationResult);
}

function setDeptLeader(dept_id, uid, relative_report) {
    var data = {leader: uid};
    data = JSON.stringify(data);
    $.post( '/api/alter_dept', {relative_report: relative_report, dept_info: data, dept_id: dept_id, op: 'update'}, operationResult);
}

function addDepartment() {
    var dept_name = $("#dept_name").val();
    if (!dept_name) {
        commonTagMsg('部门名称不能为空');
        return;
    }
    var leader_dept = $("#leader_dept").val();
    if (leader_dept === 'null') {
        leader_dept = null;
    }else {
        leader_dept = parseInt(leader_dept);
    }
    var weight = $("#dept_weight").val();
    if (!weight) {
        promptMsg('请输入权重');
        return;
    }
    if (isNaN(weight)) {
        promptMsg('权重请输入数字');
        return;
    }
    var data = {name: dept_name, parent: leader_dept, weight: weight};
    data = JSON.stringify(data);
    $.post('/api/alter_dept', {dept_info: data, op: 'add'}, operationResult);
}

function openDeptDialog(data) {
    if (data) {
        operate_dept = data.id;
        $("#dept_name").val(data.name);
        var parent_id = data.parent;
        if (!parent_id) {
            parent_id = 'null';
        } else if (!(parent_id in departments_map)) {
            parent_id = -1;
        }
        $("#leader_dept").val(parent_id).selectmenu('refresh');
        $("#dept_weight").val(data.weight);
    } else {
        $("#dept_name").val('');
        $("#dept_weight").val(0);
    }
    dept_dialog.dialog('option', 'title', getOperationString());
    dept_dialog.dialog( "open" );
}

function deleteEmployee() {
    $.post('/api/alter_account', {uid: operate_employee, op: 'del'}, operationResult);
}

function queryDepartmentEmployees(deptId) {
    selected_dept_for_employee = deptId;
    var arg = null;
    if (deptId !=="0") {
        arg = {dept_id: deptId};
    }
    $.post('/api/query_account_list', arg, setEmployeeList);
}

function setDepartmentList(data) {
    var title = ['名称', '上级部门', '主管', '权重', '删除'];
    try {
        if (data.status !== 0) {
            redirectError();
        } else {
            var dept_list = data.data;
            if (!dept_list) {
                redirectError();
            }
            if (dept_list.length === 0) {
                return;
            }
            department_list_data = dept_list;
            var listData = [];
            var options ="";
            departments_map = {};
            dept_list.forEach(function (element, index, p3) {
                departments_map[element.id] = element;
                departments_map[element.name] = element.id;
                listData.push([
                    getOperationHtml(EDIT_DEPT, index),
                    element.parent_name,
                    getDeptLeaderHtml(element),
                    element.weight,
                    getOperationHtml(DEL_DEPT, index)
                ]);
                options += "<option value='" + element.id + "'>" + element.name + "</option>"
            });
            listData.unshift(title);

            updateListView($("#dept_list"), listData, {weight: [2,2,2,1,1]});

            $("#leader_dept").append(options).selectmenu();
            $("#current_department_menu").append(options).selectmenu({
                change: function( event, ui ) {
                    var current_selected_dept = $(this).val();
                    if (selected_dept_for_employee !== current_selected_dept) {
                        removeChildren($("#employee_list"));
                        queryDepartmentEmployees(current_selected_dept);
                    }
                }
            });
            $("#belong_dept").append(options).selectmenu();
            $("#statistics_dept").append(options).selectmenu('refresh');

            initPageWhileHasCondition();
        }
    } catch (e) {
        redirectError();
    }
}

function getDeptLeaderHtml(dept) {
    var html = '<span class="common_clickable" onclick="openLeaderSettingDlg(' + dept.id + ')">';
    if (dept.leader_account) {
        html +=  dept.leader_name + '（' + dept.leader_account + '）';
    } else {
        html += '未设置';
    }
    html += '<span>';
    return html;
}

function setEmployeeList(data) {
    var title = ['账号', '姓名', '部门', '职位', '权重', '删除'];
    try {
        if (data.status !== 0 ) {
            redirectError();
        } else {
            employee_list_data = data.data;
            $("#current_employee_count").text(employee_list_data.length);
            var dataList = [];
            employee_list_data.forEach(function (element, index, p3) {
                dataList.push([
                    getOperationHtml(EDIT_EMPLOYEE, index),
                    element.name,
                    departments_map[element.department_id].name,
                    element.position,
                    getOperationHtml(SET_EMPLOYEE_WEIGHT, index),
                    getOperationHtml(DEL_EMPLOYEE, index)
                ]);
            });
            dataList.unshift(title);
            updateListView($("#employee_list"), dataList);
        }
    } catch (e) {
        alert("exception " + e);
        redirectError();
    }
}


function getOperationHtml(operation, index) {
    var label = "";
    var tip = "";

    switch (operation) {
        case EDIT_DEPT:
            label = department_list_data[index].name;
            tip = " title='编辑' ";
            break;
        case EDIT_EMPLOYEE:
            label = employee_list_data[index].account;
            tip = " title='编辑' ";
            break;
        case DEL_DEPT:
        case DEL_EMPLOYEE:
            label = "删除";
            break;
        case SET_EMPLOYEE_WEIGHT:
            label = employee_list_data[index].weight;
            break;
        case RESET_EMPLOYEE_PSD:
            label = '重置密码';
            break;
        default:
            break;
    }
    var param = operation + ', ' + index;
    return "<span class='common_clickable'" + tip + " onclick='onItemOperation(" + param  + ")'>" + label + "</span>";
}

function onItemOperation(operation, index) {
    current_operation = operation;
    switch (operation) {
        case EDIT_DEPT:
            openDeptDialog(department_list_data[index]);
            break;
        case DEL_DEPT:
            showConfirmDialog("删除该部门将会删除其子部门及归属的所有员工，慎重！确认删除该部门？", function () {
                operate_dept = department_list_data[index].id;
                dealOperation();
            });
            break;
        case EDIT_EMPLOYEE:
            window.open('employee_info_table.html?op=update&uid=' + employee_list_data[index].id);
            // openEmployeeDialog(employee_list_data[index]);
            break;
        case DEL_EMPLOYEE:
            if (employee_list_data[index].role_data <= __authority) {
                promptMsg(getOperationString() + '失败：权限不足');
                return;
            }
            showConfirmDialog("确认删除该员工？", function () {
                operate_employee = employee_list_data[index].id;
                dealOperation();
            });
            break;
        case SET_EMPLOYEE_WEIGHT:
            var employee = employee_list_data[index];
            openEmployeeWeightDlg(employee);
            break;
        case RESET_EMPLOYEE_PSD:
            operate_employee = employee_list_data[index].id;
            openEmployeePsdDlg();
            break;
        default:
            break;
    }
}

function operationResult(data) {
    try {
        if (data.status === 0) {
            freshCurrent(getResultLocation(), getLocationArgs());
        } else {
            var msg = ('msg' in data)? data['msg'] : data['status'];
            promptMsg(getOperationString() + '失败: ' + msg);
        }
    } catch (e) {
        redirectError();
    }
}

function getOperationString() {
    switch (current_operation) {
        case EDIT_DEPT:
            return '编辑部门信息';
        case ADD_DEPT:
            return '增加部门';
        case DEL_DEPT:
            return '删除部门';
        case ADD_EMPLOYEE:
            return '增加员工';
        case DEL_EMPLOYEE:
            return '删除员工';
        case EDIT_EMPLOYEE:
            return '编辑员工信息';
        case SET_DEPT_LEADER:
            return '设置部门主管';
    }
    return '无效操作';
}

function getResultLocation() {
    switch (current_operation) {
        case EDIT_DEPT:
        case ADD_DEPT:
        case DEL_DEPT:
        case SET_DEPT_LEADER:
            return 'dept_config_container';
        case ADD_EMPLOYEE:
        case DEL_EMPLOYEE:
        case EDIT_EMPLOYEE:
        case SET_EMPLOYEE_WEIGHT:
            return 'employee_config_container';
    }
    return '';
}

function getLocationArgs() {
    switch (current_operation) {
        case ADD_EMPLOYEE:
            return {dept_id: $("#belong_dept").val()};
        case EDIT_EMPLOYEE:
            return {dept_id: selected_dept_for_employee};
    }
    return null;

}

function exportEmployeeTable() {
    var param = {op: 'export'};
    var dept_id = parseInt($("#statistics_dept").val());
    if (dept_id > 0) {
        param['dept_id'] = dept_id;
    }
    param['type'] = $("#statistics_type").val();
    commonPost('/api/employee_statistics', param, function (data) {
        window.open(data);
    });
}