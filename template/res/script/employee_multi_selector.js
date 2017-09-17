

function createEmployeeMultiSelectorController(container, param) {
    var default_param = {
        dept_url: '/api/query_dept_list',
        employee_url: '/api/query_account_list?type=' + TYPE_ACCOUNT_SAMPLE,
        div_class: 'employee_list_container',
        div_btn_class: 'operation_btn_container',
        btn_class: 'operation_btn',
        filter_list: null
    };
    compareParam(default_param, param);

    var flag = (new Date()).getTime();
    var left_div = 'div_left_' + flag;
    var right_div = 'div_right_' + flag;
    var ok_btn = 'btn_ok_' + flag;
    var cancel_btn = 'btn_cancel_' + flag;
    var dept_select = 'select_' + flag;

    var controller = {
        param: default_param,
        selected_dept: null,
        left_container: null,
        left_list: null,
        left_all_btn: null,
        right_container: null,
        right_list: null,
        right_all_btn: null,
        dept_container: null,
        dept_employee_map: {},
        employee_map: {},
        all_employee_list: [],
        selected_set: new Set([]),
        init_element: function () {
            controller.left_container = $("#" + left_div);
            controller.left_list = $("#list_item_" + left_div);
            controller.left_all_btn = $("#all_item_" + left_div);
            controller.left_list.selectable({
                stop: function () {
                    controller.un_checked_all_btn(controller.left_all_btn);
                }
            });
            controller.right_container = $("#" + right_div);
            controller.right_list = $("#list_item_" + right_div);
            controller.right_all_btn = $("#all_item_" + right_div);
            controller.right_list.selectable({
                stop: function () {
                    controller.un_checked_all_btn(controller.right_all_btn);
                }
            });
            controller.dept_container = $("#" + dept_select);
            selectMenu(controller.dept_container, function (event, ui) {
                var value = parseInt($(event.target).val());
                if (value !== controller.selected_dept) {
                    controller.selected_dept = value;
                    controller.on_dept_change();
                }
            });
            controller.query_dept();
            $("input[type='checkbox']").checkboxradio();
            controller.left_all_btn.click(function () {
                var checked = $(this).is(':checked');
                controller.select_all(controller.left_list, checked);
            });
            controller.right_all_btn.click(function () {
                var checked = $(this).is(':checked');
                controller.select_all(controller.right_list, checked);
            });
        },
        un_checked_all_btn: function (btn) {
            if (btn.is(':checked')) {
                btn.attr('checked', false);
                btn.checkboxradio('refresh');
            }
        },
        on_dept_change: function () {
            controller.fresh_left();
        },
        on_ok: function () {
            controller.un_checked_all_btn(controller.left_all_btn);
            controller.un_checked_all_btn(controller.right_all_btn);

            var selected = false;
            controller.left_list.children('.ui-selected').each(function () {
                selected = true;
               var id = $(this).val();
               var employee = controller.employee_map[id];
               employee['selected'] = true;
               controller.selected_set.add(id);
            });
            if (selected) {
                controller.fresh();
            }
        },
        on_cancel: function () {
            controller.un_checked_all_btn(controller.left_all_btn);
            controller.un_checked_all_btn(controller.right_all_btn);

            var selected = false;
            controller.right_list.children('.ui-selected').each(function () {
                selected = true;
                var id = $(this).val();
                var employee = controller.employee_map[id];
                employee['selected'] = false;
                controller.selected_set.delete(id);
            });
            if (selected) {
                controller.fresh();
            }
        },
        fresh: function () {
            controller.fresh_left();
            controller.fresh_right();
        },
        fresh_left: function () {
            if (controller.selected_dept === null || controller.selected_dept === undefined) {
                return;
            }
            var selectable_employee = null;
            if (controller.selected_dept === 0) {
                selectable_employee = controller.all_employee_list;
            } else {
                selectable_employee = controller.dept_employee_map[controller.selected_dept];
            }
            var list_data = '';
            selectable_employee.forEach(function (p1, p2, p3) {
                if (!p1.selected) {
                    list_data += controller.get_employee_item_html(p1);
                }
            });
            removeChildren(controller.left_list);
            controller.left_list.append(list_data).selectable('refresh');
        },
        select_all: function (container, selected) {
            if (selected) {
                container.children('li').each(function () {
                    $(this).addClass('ui-selected');
                });
            } else {
                container.children('li').each(function () {
                    $(this).removeClass('ui-selected');
                });
            }
        },
        fresh_right: function () {
            var list_data = '';
            controller.selected_set.forEach(function (p1, p2, p3) {
                list_data += controller.get_employee_item_html(controller.employee_map[p1]);
            });
            removeChildren(controller.right_list);
            controller.right_list.append(list_data).selectable('refresh');
        },
        get_employee_item_html: function (item) {
            return '<li value="' + item.id + '">' + item.dept + '　' + item.name + '　' + item.position + '</li>';
        },
        query_dept: function () {
            commonPost(controller.param.dept_url, null, function (data) {
                var options = '';
                data.forEach(function (p1, p2, p3) {
                    options += '<option value="' + p1.id + '">' + p1.name + '</option>';
                    controller.dept_employee_map[p1.id] = [];
                });
                controller.dept_container.append(options).selectmenu('refresh');
                controller.query_employee();
            });
        },
        query_employee: function () {
            var filter_map = null;
            if (controller.param.filter_list) {
                filter_map = {};
                controller.param.filter_list.forEach(function (p1, p2, p3) {
                   filter_map[p1] = p1;
                });
            }
            commonPost(controller.param.employee_url, null, function (data) {
                data.forEach(function (p1, p2, p3) {
                    if (filter_map && filter_map.hasOwnProperty(p1.id)) {
                        return;
                    }
                    controller.all_employee_list.push(p1);
                    p1['selected'] = false;
                    controller.dept_employee_map[p1.department_id].push(p1);
                    controller.employee_map[p1.id] = p1;
                });
            });
        },
        remove_item: function (id) {
            controller.employee_map[id].selected = false;
            controller.selected_set.delete(id);
        },
        get_result: function () {
            return controller.selected_set;
        }
    };

    var html = '';
    html += '<div class="common_btn_container">';
    html += '<select id="' + dept_select + '">';
    html += '<option selected disabled value="-1">请选择部门</option>';
    html += '<option value="0">全部</option>';
    html += '</select>';
    html += '</div>';
    html += getEmployeeListContainerHtml(left_div, default_param.div_class);
    html += '<div class="' + default_param.div_btn_class + '">';
    html += '<div><button class="ui-button ui-corner-all ' + default_param.btn_class + '" id="' + ok_btn + '">　>>　</button></div>';
    html += '<div><button class="ui-button ui-corner-all ' + default_param.btn_class + '" id="' + cancel_btn + '">　<<　</button></div>';
    html += '</div>';
    html += getEmployeeListContainerHtml(right_div, default_param.div_class);
    container.append(html);
    controller.init_element();
    $("#" + ok_btn).click(function() {
        controller.on_ok();
    });
    $("#" + cancel_btn).click(function() {
        controller.on_cancel();
    });

    return controller;
}

function getEmployeeListContainerHtml(id, container_class) {
    var item =  '<div id="' + id + '" class="' + container_class + '">';
    var all_id = 'all_item_' + id;
    item += '<div><input type="checkbox" name="' + all_id + '" id="' + all_id + '"><label for="' + all_id + '">全选</label> </div>';
    var list_id = 'list_item_' + id;
    item += '<div><ul class="employee_selectable_list" id="' + list_id + '"></ul></div>';
    item += '</div>';
    return item;
}