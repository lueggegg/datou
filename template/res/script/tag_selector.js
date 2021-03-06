var __tag_map = {};

function createListSelectorController(container, param) {
    var controller = {
        data: param.data,
        checkbox: null,
        get_result: function() {
            var result = [];
            $("[name='" + this.checkbox + "']").filter(':checked').each(function () {
                result.push($(this).val());
            });
            return result;
        },
        is_radio: param.is_radio
    };

    var html = '';
    var checkbox_name = 'checkbox_' + param.name;
    controller.checkbox = checkbox_name;
    var input_type = param.is_radio? 'radio' : 'checkbox';
    param.data.forEach(function (p1, p2, p3) {
        html += '<div class="common_container">';
        var id = param.name + '_item_' + p1.id;
        html += '<input type="' + input_type + '" name="' + checkbox_name + '" value="' + p1.id + '" id="' + id + '">';
        html += '<label for="' + id + '">' + p1.label + '</label>';
        html += '</div>';
    });
    container.append(html);
    $("[name='" + checkbox_name +"']").checkboxradio({icon: false});

    return controller;
}

function createTagSelectorController(container, param) {
    var controller = {
        container: container,
        param: param,
        get_result: function () {
                var type_list = [];
                var value_list = [];
                for (var key in __tag_map) {
                    if (__tag_map.hasOwnProperty(key)) {
                        var tag = __tag_map[key];
                        if (!tag.checked) continue;
                        if (tag.all) {
                            type_list.push(key);
                        } else if (tag.leader){
                            value_list.push(tag.type.leader);
                        }else {
                            tag.selected_values.forEach(function (p1, p2, p3) {
                                value_list.push(p1);
                            });
                        }
                    }
                }
                var result = {status: 0};
                if (type_list.length > 0) {
                    result.status |= 1;
                    result['type_list'] = type_list;
                }
                if (value_list.length > 0) {
                    result.status |= 2;
                    result['value_list'] = value_list;
                }
                return result;
            },
        reset: function () {

        }
    };

    commonPost(param.type_url, null, function (data) {
        data.forEach(function (p1, p2, p3) {
            __tag_map[p1.id] = {type: p1};
        });
        initTagSelectorContainer(controller);
    });

    return controller;
}


function initTagSelectorContainer(controller) {
    var container = controller.container;
    for (var key in __tag_map) {
        if (__tag_map.hasOwnProperty(key)) {
            createTagSelector(controller, key)
        }
    }
    $("[name='__tag_checkbox']").checkboxradio();
    $(".tag_selector_checkbox").on('change', function (event) {
        var target = $(event.target);
        var checked = target.is(":checked");
        var tag_id = parseInt(target.val());
        var tag = __tag_map[tag_id];
        tag['checked'] = checked;
        if (checked) {
            tag.selector_radio.show();
            if (tag.selector_radio_value !== 0) {
                tag.value_selector.show();
            }
        } else {
            tag.selector_radio.hide();
            tag.value_selector.hide();
        }
    });
}

/*
    tag {
        type: {
            name: abc
        },
        values: [],
        checked: false,
        all: false,
        leader: false,
        selected_values: [],
        selector_radio_value: 0/1,
        selector_radio: ui,
        value_selector: ui
    }
 */
function createTagSelector(controller, tag_id) {
    var tag = __tag_map[tag_id];
    var html = "<div class='tag_selector' id='__tag_selector_" + tag_id + "'>";
    var checkbox_id = '__tag_checkbox_' + tag_id;
    html += "<input type='checkbox' class='tag_selector_checkbox' name='__tag_checkbox' value='" + tag_id + "' id='" + checkbox_id + "'>";
    html += "<label for='" + checkbox_id + "'>" + tag.type.name + "</label>";
    var radio_id = [
        '__radio_tag_all_' + tag_id,
        '__radio_tag_unfold_' + tag_id,
        '__radio_tag_leader_' + tag_id
    ];
    var radio_label = ['全部', '展开', '主管'];
    var radio_check = ['checked', ''];
    var radio_container_id = '__tag_selector_radio_' + tag_id;
    var radio_name = '__radio_tag_selector_' + tag_id;
    html += "<span id='" + radio_container_id + "'>";
    radio_id.forEach(function (p1, p2, p3) {
        html += "<input class='tag_selector_radio' type='radio' " + radio_check[p2] + " value='" + p2 + "' name='" + radio_name + "' id='" + p1 + "'>";
        html += "<lable for='" + p1 + "'>" + radio_label[p2] + "</lable>";
    });
    html += "</span>";
    html += "</div>";
    html += "<div class='tag_value_selector' id='tag_value_selector_" + tag_id + "'></div>";
    controller.container.append(html);

    tag['selector_radio'] = $("#" + radio_container_id);
    tag.selector_radio.hide();
    tag['selector_radio_value'] = 0;
    tag['value_selector'] = $("#tag_value_selector_" + tag_id);
    tag.value_selector.hide();
    tag['checked'] = false;
    tag['all'] = true;
    tag['leader'] = false;
    tag['selected_values'] = [];
    $("[name='" + radio_name + "']").on('change', function(event) {
        var value = parseInt($(event.target).val());
        tag.selector_radio_value = value;
        if (value === 0) {
            tag.value_selector.hide();
            tag.all = true;
            tag.leader = false;
        } else if (value === 2) {
            if (!tag.type.leader) {
                promptMsg('该部门未设置主管');
            }
            tag.value_selector.hide();
            tag.all = false;
            tag.leader = true;
        }else {
            if (!tag.values) {
                commonPost(controller.param.value_url, controller.param.get_value_url_arg(tag_id), function (data) {
                    __tag_map[tag_id].values = data;
                    initTagValueSelector(data, tag_id, controller.param);
                });
            }
            tag.value_selector.show();
            tag.all = false;
            tag.leader = false;
        }
    });
}

function initTagValueSelector(list_data, tag_id, param) {
    if (list_data.length === 0) return;
    var item_name = '__tag_value_selector_item_in_' + tag_id;
    var html = "";
    list_data.forEach(function (p1, p2, p3) {
        if (param.filter_list && param.filter_list.hasOwnProperty(p1.id)) {
            return;
        }
        var item_id = '__tag_value_selector_item_' + p1.id;
        html += "<input type='checkbox' value='" + p1.id + "' name='" + item_name + "' id='" + item_id + "'>";
        html += "<label for='" + item_id + "'>" + param.get_value_label(p1) + "</label>";
    });
    var tag = __tag_map[tag_id];
    tag.value_selector.append(html);
    var checkboxs = $("[name='" + item_name + "']");
    checkboxs.checkboxradio({icon: false});
    checkboxs.on('change', function (event) {
        var target = $(event.target);
        var checked = target.is(":checked");
        var value_id = target.val();
        if (checked) {
            tag.selected_values.push(value_id);
        } else {
            tag.selected_values.some(function (p1, p2, p3) {
                if (p1 === value_id) {
                    tag.selected_values.splice(p2, 1);
                    return true;
                }
                return false;
            });
        }
    });
}