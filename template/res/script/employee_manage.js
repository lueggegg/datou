var dept_dialog = null;
var import_employees_dlg = null;
var import_employees_result_dlg = null;
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
var SET_AS_LEADER = 13;
var SET_DEPT_LEADER = 20;
var current_operation = NULL_OPERATION;

var dept_leader_setting_dlg;

$(document).ready(function () {

    verticalTabs("#tabs");

    dept_dialog = $( "#edit_dept_dialog" );
    employee_dialog = $("#edit_employee_dialog");
    dept_leader_setting_dlg = $("#edit_dept_leader_dlg");

    initDialog(dept_dialog);
    initDialog(employee_dialog, 450);
    initDialog(dept_leader_setting_dlg);

    $( "#add_dept" ).click(function( event ) {
        current_operation = ADD_DEPT;
        openDeptDialog('增加部门', '', 'null');
    });

    $( "#add_employee" ).click(function( event ) {
        current_operation = ADD_EMPLOYEE;
        openEmployeeDialog();
    });

    $("#reset_employee_password").click(function (event) {
        if (__authority > __admin_authority) {
            promptMsg('没有权限');
            return;
        }
        enableResetEmployeePassword(true);
        event.preventDefault();
    });
    $("#cancel_reset_employee_password").click(function (event) {
        enableResetEmployeePassword(false);
        event.preventDefault();
    });

    selectMenu($("#current_department_menu"));
    selectMenu($("#leader_dept"));
    selectMenu($("#belong_dept"));
    selectMenu($("#dept_leader_selector"));
    selectMenu($("#position_selector"));
    initPositionSelector();

    initDatePicker($("#join_date"), function (dateText, inst) {
        join_date = dateText;
    }, true);
    initDatePicker($("#birthday"), function (dateText, inst) {
        birthday = dateText;
    });

    $.post('/api/query_dept_list', null, setDepartmentList) ;

    initPromptDialog();
    initConfirmDialog();
});

function initPageWhileHasCondition() {
    if (__dept_id) {
        $("#current_department_menu").val(__dept_id).selectmenu('refresh');
        queryDepartmentEmployees(__dept_id);
    }
}

function initPositionSelector() {
    var positions = ['主任', '副主任', '一级主管', '二级主管', '一级员工', '临聘员工'];
    var options = '';
    positions.forEach(function (p1, p2, p3) {
        options += '<option value="' + p1 + '">' + p1 + '</option>';
    });
    $("#position_selector").append(options).selectmenu('refresh');
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
        case EDIT_EMPLOYEE:
            updateEmployee();
            break;
        case ADD_EMPLOYEE:
            addEmployee();
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
            setDeptLeader(selected_dept, uid);
            break;
    }
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
        commonTagMsg('部门名称不能为空');
        return;
    }
    var leader_dept = $("#leader_dept").val();
    if (leader_dept === 'null') {
        if (__authority > __admin_authority) {
            commonTagMsg('权限不足（非管理员不能设置上级部门为空）');
            return;
        }
        leader_dept = null;
    } else {
        leader_dept = parseInt(leader_dept);
    }
    if (leader_dept === operate_dept) {
        commonTagMsg('不能将自身作为上级部门');
        return;
    }
    var data = {name: dept_name, parent: leader_dept};
    data = JSON.stringify(data);
    $.post( '/api/alter_dept', {dept_info: data, dept_id: operate_dept, op: 'update'}, operationResult);
}

function deleteDepartment() {
    $.post('/api/alter_dept', {dept_id: operate_dept, op: 'del'}, operationResult);
}

function setDeptLeader(dept_id, uid) {
    var data = {leader: uid};
    data = JSON.stringify(data);
    $.post( '/api/alter_dept', {dept_info: data, dept_id: dept_id, op: 'update'}, operationResult);
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
    var data = {name: dept_name, parent: leader_dept};
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
    } else {
        $("#dept_name").val('');
    }
    dept_dialog.dialog('option', 'title', getOperationString());
    dept_dialog.dialog( "open" );
}

function enableResetEmployeePassword(enable, hide_cancel_btn) {
    operate_reset_employee_password = enable;
    var password_editor = $("#employee_password");
    var password_reset_btn = $("#reset_employee_password");
    var cancel_btn = $("#cancel_reset_employee_password");
    if (enable) {
        password_editor.show();
        password_reset_btn.hide();
        if (hide_cancel_btn) {
            cancel_btn.hide();
        } else {
            cancel_btn.show();
        }
    } else {
        password_editor.hide();
        password_reset_btn.show();
        cancel_btn.hide();
    }
}

function openEmployeeDialog(data) {
    var account_item = $("#employee_account");
    var password_editor = $("#employee_password");
    var password_reset_btn = $("#reset_employee_password");
    password_editor.val("");
    portrait_data = null;
    $("#portrait_file").val('');
    if (!data) {
        account_item[0].disabled = false;
        account_item.val("");
        $("#personal_portrait").attr('src', 'res/images/default_portrait.png');
        $("#employee_name").val("");
        $("#id_card").val('');
        $("#belong_dept").val(-1).selectmenu('refresh');
        $("#position_selector").val(-1).selectmenu('refresh');
        $("#join_date").datepicker('setDate', new Date());
        join_date = $("#join_date").val();
        $("#cellphone").val('');
        $("#birthday").val('');
        birthday = null;
        enableResetEmployeePassword(true, true);
    } else {
        operate_employee = data.id;
        operate_employee_authority = data.authority;
        account_item[0].disabled = true;
        account_item.val(data.account);
        $("#personal_portrait").attr('src', data.portrait);
        $("#employee_name").val(data.name);
        $("#id_card").val(data.id_card);
        $("#belong_dept").val(data.department_id).selectmenu('refresh');
        $("#position_selector").val(data.position).selectmenu('refresh');
        $("#join_date").val(data.join_date);
        join_date = null;
        if (data.cellphone) {
            $("#cellphone").val(data.cellphone);
        }
        $("#birthday").val(data.birthday? data.birthday : '');
        enableResetEmployeePassword(false);
    }
    employee_dialog.dialog('option', 'title', getOperationString());
    employee_dialog.dialog('open');
}

var portrait_data = null;
function onPortrailChange() {
    var files = $("#portrait_file")[0].files;
    if (files.length === 0) {
        return;
    }
    var f = files[0];
    var reader = new FileReader();
    reader.onload = function (e) {
        portrait_data = e.target.result;
        $("#personal_portrait").attr('src', portrait_data);

    };
    reader.readAsDataURL(f);
}

function addEmployee() {
    if (!portrait_data) {
        promptMsg('请选择证件照');
        return;
    }
    var account = $("#employee_account").val();
    if (!account) {
        promptMsg("账号不能为空");
        return;
    }
    var name = $("#employee_name").val();
    if (!name) {
        promptMsg('姓名不能为空');
        return;
    }
    var id_card = $("#id_card").val();
    if (!id_card) {
        promptMsg('身份证不能为空');
        return;
    }
    if (!isValidIdCard(id_card)) {
        promptMsg('无效的身份证');
        return;
    }
    var dept_id = $("#belong_dept").val();
    if (!dept_id || dept_id === -1) {
        promptMsg('请选择部门');
        return;
    }
    var position = $("#position_selector").val();
    if (!position || position === '-1') {
        promptMsg('请选择职位');
        return;
    }
    var password = $("#employee_password").val();
    if (!password) {
        password = 'oa123456';
    }
    password = getHash(password);

    var data = {
        portrait: portrait_data,
        account: account,
        password: password,
        name:name,
        id_card: id_card,
        department_id: dept_id,
        position: position,
        join_date: join_date
    };

    var phone = $("#cellphone").val();
    if (phone) {
        if (!isValidPhoneNumber(phone)) {
            promptMsg('不合法的手机号');
            return;
        }
        data['cellphone'] = phone;
    }
    if (birthday) {
        data['birthday'] = birthday;
    }
    data = JSON.stringify(data);
    $.post('/api/alter_account', {account_info: data, op: 'add'}, operationResult);
}

function updateEmployee() {
    // if (operate_employee_authority <= __authority) {
    //     promptMsg(getOperationString() + '失败：权限不足');
    //     return;
    // }
    var account = $("#employee_account").val();
    if (!account) {
        promptMsg("账号不能为空");
        return;
    }
    var name = $("#employee_name").val();
    if (!name) {
        promptMsg('姓名不能为空');
        return;
    }
    var id_card = $("#id_card").val();
    if (!id_card) {
        promptMsg('身份证不能为空');
        return;
    }
    if (!isValidIdCard(id_card)) {
        promptMsg('无效的身份证');
        return;
    }
    var dept_id = $("#belong_dept").val();
    if (!dept_id || dept_id === -1) {
        promptMsg('请选择部门');
        return;
    }
    var position = $("#position_selector").val();
    if (!position || position === '-1') {
        promptMsg('请选择职位');
        return;
    }

    var phone = $("#cellphone").val();
    if (phone && !isValidPhoneNumber(phone)) {
        promptMsg('不合法的手机号');
        return;
    }

    var data = {
        name:name,
        id_card: id_card,
        department_id: dept_id,
        position: position,
        cellphone: phone
    };
    if (join_date) {
        data['join_date'] = join_date;
    }

    if (operate_reset_employee_password) {
        var password = $("#employee_password").val();
        if (!password) {
            password = 'oa123456';
        }
        password = getHash(password);
        data['password'] = password;
    }

    if (portrait_data) {
        data['portrait'] = portrait_data;
    }
    if (birthday) {
        data['birthday'] = birthday;
    }

    data = JSON.stringify(data);
    $.post('/api/alter_account', {account_info: data, uid: operate_employee, op: 'update'}, operationResult);
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
    var title = ['名称', '上级部门', '主管', '删除'];
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
                    getOperationHtml(DEL_DEPT, index)
                ]);
                options += "<option value='" + element.id + "'>" + element.name + "</option>"
            });
            listData.unshift(title);

            updateListView($("#dept_list"), listData);

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
    var title = ['账号', '姓名', '部门', '职位', '操作', '删除'];
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
                    getOperationHtml(SET_AS_LEADER, index),
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
        case SET_AS_LEADER:
            label = '设为部门主管';
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
            openEmployeeDialog(employee_list_data[index]);
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
        case SET_AS_LEADER: {
                var employee = employee_list_data[index];
                var dept = departments_map[employee.department_id];
                if (dept.leader) {
                    if (dept.leader === employee.id) {
                        promptMsg('该员工已经是部门主管');
                        return;
                    }
                    showConfirmDialog('该部门已经存在主管，是否变更主管?', function () {
                        setDeptLeader(employee.department_id, employee.id);
                    });
                } else{
                    setDeptLeader(employee.department_id, employee.id);
                }
            }
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
        case SET_AS_LEADER:
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