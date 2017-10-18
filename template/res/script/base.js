var __my_uid = null;
var __authority = null;
var __my_operation_mask = null;

var __super_authority = 1;
var __admin_authority = 8;
var __dept_leader_authority = 16;
var __common_authority = 1024;

var NULL_OPERATION = -1;
var __current_operation = NULL_OPERATION;

function redirectError(e) {
    if (e) {
        console.debug('exception: ' + e);
    }
    window.location.href = 'error.html?message=' + encodeURI('exception: ' + e);
}

function needAuthority(operation_mask) {
    if (!isAuthorized(operation_mask)) {
        redirectError('没有权限');
    }
}

function isAuthorized(operation_mask) {
    return __authority <= __admin_authority || (__my_operation_mask & operation_mask) !== 0;
}

function freshCurrent(location, args) {
    var param = '';
    if (args) {
        for (var key in args) {
            if (args.hasOwnProperty(key)) {
                param += '&' + key + '=' + args[key];
            }
        }
    }

    window.location.href = '?update=' + Math.random() + param + '#' + location;
}

function getHash(str) {
    return hex_sha1(hex_md5(str));
}

function removeChildren(container) {
    container.children().remove();
}

function selectMenu(container, onChange) {
    container.selectmenu({
        width: 230,
        change: onChange
    });
}

function verticalTabs(target_id) {
    if (!target_id) target_id = "#tabs";
    $( target_id ).tabs().addClass( "ui-tabs-vertical ui-helper-clearfix" );
    $( target_id + " li" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-left" )
}

function isValidPhoneNumber(number) {
    return number.length === 11 && parseInt(number) > 10000000000;
}

function isValidIdCard(id_card) {
    var valid = true;
    valid &= id_card.length === 18;
    if (!valid) {
        return false;
    }
    var divider = [[0,6], [6,10], [10,12], [12,14], [14,17]];
    var limit = [[100000, 999999], [1900,2017], [0,12], [0,31], [0,999]];
    valid &= divider.every(function (p1, p2, p3) {
        var num = parseInt(id_card.slice(p1[0], p1[1]));
        return num > limit[p2][0] && num <= limit[p2][1];
    });
    return valid;
}

function compareParam(default_param, param) {
    if (!param) return;
    for (var key in param) {
        if (param.hasOwnProperty(key)) {
            default_param[key] = param[key];
        }
    }
}
function updateListView(container, data, param) {
    if (!(param && param.hasOwnProperty('keep_children'))) {
        removeChildren(container);
    }
    container.append(getListViewHtml(data, param));
}

function getListViewHtml(data, param){

    var default_param = {
        without_title: false,
        weight: null,
        diff_background: true,
        ul_class: 'list_view_ul',
        item_callback: null
    };
    compareParam(default_param, param);

    var total = 98;
    var content = "";
    var item_size = data[0].length;
    var widths = [];
    var background = [default_param.diff_background?' list_view_ul_even_row':'', ''];
    if (default_param.weight && default_param.weight.length === item_size) {
        var total_weight = 0;
        default_param.weight.forEach(function (p1, p2, p3) {
            total_weight += p1;
        });
        default_param.weight.forEach(function (p1, p2, p3) {
            widths.push(Math.floor(p1/total_weight*total));
        })
    } else {
        for (var i = 0; i < item_size; ++i) {
            widths.push(Math.floor(total/item_size));
        }
    }

    data.forEach(function (p1, p2, p3) {
       if (p2 === 0 && !default_param.without_title) {
           content += "<ul class='th " + default_param.ul_class + "'>";
       } else {
           content += "<ul class='" + default_param.ul_class + background[p2 % 2] + "'>";
       }
        p1.forEach(function (field, index, p) {
            content += "<li style='width: " + widths[index] + "%'>" + field + "</li>";
        });
        content += "</ul>";
    });
    return content;
}

var __common_waiting_dlg;
var __common_waiting_timeout;
function initCommonWaitingDialog(timeout_cb) {
    if (__common_waiting_dlg) return;

    var html = "<div id='__common_waiting_dlg' title='请等待'>";
    html += "<div id='__common_waiting_bar' class='common_border'><div class='progress_label'>processing ...</div></div>";
    html += "</div>";
    $("body").append(html);
    __common_waiting_dlg = $("#__common_waiting_dlg");
    __common_waiting_dlg.dialog({
        width: 240,
        modal: true,
        autoOpen: false
    });
    $("#__common_waiting_bar").progressbar({
        value: false
    });
}

function showWaitingDlg(param) {
    if (!__common_waiting_dlg) return;

    var default_param = {
        timeout: 10000,
        timeout_cb: null
    };
    compareParam(default_param, param);

    __common_waiting_dlg.dialog('open');
    __common_waiting_timeout = setTimeout(function () {
        closeWaitingDlg();
        if (default_param.timeout_cb) {
            default_param.timeout_cb();
        }
    }, default_param.timeout);
}

function closeWaitingDlg() {
    if (!__common_waiting_dlg) return;

    clearTimeout(__common_waiting_timeout);
    __common_waiting_timeout = null;
    __common_waiting_dlg.dialog('close');
}

var __common_confirm_dlg;
var __common_confirm_dlg_callback;
function initConfirmDialog() {
    var html = "<div id='__common_confirm_dlg' title='确认操作'><p id='__common_confirm_dlg_info' class='common_prompt_info'>info</p><p>&nbsp;</p></div>";
    $("body").append(html);
    __common_confirm_dlg = $("#__common_confirm_dlg");
    __common_confirm_dlg.dialog({
        autoOpen: false,
        width: 400,
        modal: true,
        buttons: [
            {
                text: "继续",
                click: function() {
                    if (__common_confirm_dlg_callback) {
                        __common_confirm_dlg_callback();
                    }
                    __common_confirm_dlg_callback = null;
                    $( this ).dialog( "close" );
                }
            },
            {
                text: "取消",
                click: function () {
                    $( this ).dialog( "close" );
                }
            }
        ]
    });
}

function showConfirmDialog(msg, continue_callback) {
    if (__common_confirm_dlg) {
        __common_confirm_dlg_callback = continue_callback;
        $("#__common_confirm_dlg_info").html(msg);
        __common_confirm_dlg.dialog('open');
    }
}

var __common_prompt_dlg = null;
function initPromptDialog(modal) {
    if (__common_prompt_dlg) return;

    modal = !!modal;
    var html = "<div id='__common_prompt_dlg' title='提示'><p id='__common_prompt_dlg_info' class='common_prompt_info'>info</p><p>&nbsp;</p></div>";
    $("body").append(html);
    __common_prompt_dlg = $("#__common_prompt_dlg");
    __common_prompt_dlg.dialog({
        autoOpen: false,
        width: 400,
        modal: modal,
        buttons: [
            {
                text: "确定",
                click: function() {
                    $( this ).dialog( "close" );
                }
            }
        ]
    });
}

function promptMsg(msg, millis) {
    if (__common_prompt_dlg) {
        $("#__common_prompt_dlg_info").html(msg);
        __common_prompt_dlg.dialog('open');
        if (!millis) {
            millis = 2000;
        }
        setTimeout(function () {
            __common_prompt_dlg.dialog('close')
        }, millis);
    }
}

function commonTagMsg(msg) {
    $("#__common_tag_area").show();
    $("#__common_tag_area").text(msg);
    setTimeout(function () {
        $("#__common_tag_area").text('');
    }, 3000);
}

function initDatePicker(container, param) {
    // var param = {
    //     dateFormat: "yy-mm-dd",
    //     changeYear: true,
    //     defaultDate : new Date(),
    //     onSelect: on_select_cb
    // };
    var default_param = {
        timepicker: false,
        format: 'Y-m-d'
    };
    compareParam(default_param, param);
    container.datetimepicker(default_param);
}

function consoleDebug(msg) {
    console.debug(msg);
}

function commonSelectable(container, onSelected, filter) {
    if (!filter) filter = 'li';

    container.selectable({
        first_selecting: null,
        last_selected: null,

        selecting: function (event, ui) {
            if (!this.first_selecting) {
                this.first_selecting = ui.selecting.value;
            }
        },

        stop: function (event, ui) {
            if (this.first_selecting) {
                this.last_selected = this.first_selecting;
            }
            this.first_selecting = null;
            var container = $(event.target);
            container.children(this.filter).removeClass('ui-selected');
            if (this.last_selected) {
                var value = this.last_selected;
                container.children(this.filter).filter(function () { return $(this).val() === value; }).addClass('ui-selected');
                if (onSelected) {
                    onSelected(this.last_selected);
                }
            }
        },

        filter: filter
    })
}

function commonInitDialog(dialog, onOK, param) {
    var default_param = {
        width: 400,
        modal: true,
        with_ok_btn: true
    };
    compareParam(default_param, param);

    var buttons = [];
    if (default_param.with_ok_btn) {
        buttons.push({
            text: "确定",
            click: onOK
        });
    }
    buttons.push({
        text: "取消",
        click: function() {
            dialog.dialog( "close" );
        }
    });
    dialog.dialog({
        autoOpen: false,
        modal: default_param.modal,
        width: default_param.width,
        buttons: buttons
    });
}

function abstractDateFromDatetime(datetime) {
    return datetime.slice(0, 10);
}

function commonPost(url, param, successCallback, block) {
    $.post(url, param, function (data) {
        if (block) {
            closeWaitingDlg();
        }
        try {
            if (data.status !== 0) {
                if (data.hasOwnProperty('msg')) {
                    promptMsg(data.msg);
                } else {
                    promptMsg('服务器错误');
                }
                return;
            }
            if (successCallback) {
                successCallback(data.data);
            }
        } catch (e) {
            redirectError(e);
        }
    });
    if (block) {
        showWaitingDlg({timeout_cb: function () {
            promptMsg('响应超时，即将刷新页面');
            setTimeout(function () {
                window.location.reload();
            }, 1000);
        }});
    }
}

function html2Text(sHtml) {
    sHtml = sHtml.replace(/(<br\/>|<br>)/ig, '\n');
    return sHtml.replace(/[ <>&"\n\r]/g,function(c){
        return {
            ' ': '&nbsp;',
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            '\n': "<br/>",
            '\r': "<br/>"
        }[c];
    });
}

function commonGetString(str, default_value) {
    if (!default_value) {
        default_value = '无';
    }
    if (!str) {
        return default_value;
    }
    return str;
}

function wrapJobContent(content) {
    return '{' + content + '}';
}

function abstractJobContent(content) {
    return content.slice(1, content.length-1);
}

function wrapWithSpan(item) {
    return '<span>' + item + '</span>';
}

var job_type_map = {};
job_type_map[TYPE_JOB_OFFICIAL_DOC] = '公文';
job_type_map[TYPE_JOB_CERTIFICATE_SALARY] = '收入证明';
job_type_map[TYPE_JOB_CERTIFICATE_LABOR] = '工作证明';
job_type_map[TYPE_JOB_CERTIFICATE_MARRIAGE] = '婚育证明';
job_type_map[TYPE_JOB_CERTIFICATE_INTERNSHIP] = '实习证明';
job_type_map[TYPE_JOB_HR_RESIGN] = '离职申请';
job_type_map[TYPE_JOB_HR_RECOMMEND] = '伯乐推荐';
job_type_map[TYPE_JOB_HR_ANOTHER_POST] = '调岗申请';
job_type_map[TYPE_JOB_HR_ASK_FOR_LEAVE] = '请假流程';
job_type_map[TYPE_JOB_ASK_FOR_LEAVE_LEADER_BEYOND_ONE_DAY] = '中层请假';
job_type_map[TYPE_JOB_ASK_FOR_LEAVE_LEADER_IN_ONE_DAY] = '中层请假';
job_type_map[TYPE_JOB_ASK_FOR_LEAVE_NORMAL_BEYOND_ONE_DAY] = '员工请假';
job_type_map[TYPE_JOB_ASK_FOR_LEAVE_NORMAL_IN_ONE_DAY] = '员工请假';
job_type_map[TYPE_JOB_HR_LEAVE_FOR_BORN] = '产假流程';
job_type_map[TYPE_JOB_LEAVE_FOR_BORN_LEADER] = '中层产假';
job_type_map[TYPE_JOB_LEAVE_FOR_BORN_NORMAL] = '员工产假';
job_type_map[TYPE_JOB_FINANCIAL_PURCHASE] = '购物流程';
job_type_map[TYPE_JOB_FINANCIAL_REIMBURSEMENT] = '报销流程';
job_type_map[TYPE_JOB_DOC_REPORT] = '呈报表';
job_type_map[TYPE_JOB_APPLY_RESET_PSD] = '重置密码';
job_type_map[TYPE_JOB_SYSTEM_MSG] = '系统消息';
