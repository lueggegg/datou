
var __super_authority = 1;
var __admin_authority = 8;
var __dept_leader_authority = 16;
var __common_authority = 1024;

function redirectError(e) {
    if (e) {
        window.console.debug('exception: ' + e);
    }
    alert('error');
    // window.location.href = 'error.html';
}

function freshCurrent(location) {
    window.location.href = '?update=' + Math.random() + '#' + location;
}

function getHash(str) {
    return hex_sha1(hex_md5(str));
}

function removeChildren(container) {
    container.children().remove();
}

function selectMenu(container) {
    container.selectmenu({
        width: 230
    });
}

function verticalTabs(target_id) {
    $( target_id ).tabs().addClass( "ui-tabs-vertical ui-helper-clearfix" );
    $( target_id + " li" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-left" )
}

function isValidPhoneNumber(number) {
    return number.length === 11 && parseInt(number)>= 10000000000;
}
function updateListView(container, data, without_title){
    removeChildren(container);

    var content = "";
    var i = 0;
    var length = data.length;
    var li_style =  "";
    if (!without_title) {
        content += "<ul class='th list_view_ul'>";
        var item = data[i];
        var item_size = item.length;
        li_style += "width: " + Math.floor(100/item_size) + "%;";
        for (var j = 0; j < item_size; ++j) {
            content += "<li style='" + li_style + "'>" + item[j] + "</li>"
        }
        content += "</ul>";
        i++;
    }
    for (; i < length; ++i) {
        content += "<ul class='list_view_ul'>";
        var item = data[i];
        for (var j = 0; j < item.length; ++j) {
            content += "<li style='" + li_style + "'>" + item[j] + "</li>"
        }
        content += "</ul>";
    }
    container.append(content);
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

var __common_prompt_dlg;
function initPromptDialog(modal) {
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

function initDatePicker(container, onSelectCb) {
    container.datepicker({
        dateFormat: "yy-mm-dd",
        changeYear: true,
        maxDate: "0d",
        defaultDate : new Date(),
        onSelect: onSelectCb
    });
    container.datepicker("setDate", new Date());
}