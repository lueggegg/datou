var __next_controller_id = 1;
var __controller_map = {};
var __next_fid = 1;
var __file_map = {};
var __max_upload_file_size = 16 * 1024 * 1024;

function getNextControllerId() {
    var ret = __next_controller_id;
    __next_controller_id++;
    return ret;
}

function getNextFileId() {
    var ret = __next_fid;
    __next_fid++;
    return ret;
}

function registerController(id, controller) {
    __controller_map[id] = controller;
}

function initAttachmentController(container, param) {
    var default_param = {
        ul_class: 'attachment_list',
        type: TYPE_JOB_ATTACHMENT_NORMAL,
        label: '上传附件'
    };
    compareParam(default_param, param);

    var controller_id = getNextControllerId();
    var outer_id = '__attachment_' + controller_id;
    var controller = {
        id: controller_id,
        type: default_param.type,
        outer: "#" + outer_id,
        change: function() {
            var file_selector = $(this.outer + " input");
            var files = file_selector[0].files;
            if (files.length === 0) {
                return;
            }
            var f = files[0];
            file_selector.val('');
            if (f.size > __max_upload_file_size) {
                promptMsg('上传的文件过大');
                return;
            }
            var fid = getNextFileId();
            var item_data = {fid: fid, name: f.name};
            addAttachmentItem($(this.outer + " ul"), item_data, this.type);
            var file_obj = {id: fid, file: f, upload: false};
            this.files[fid] = file_obj;
            uploadAttachment(file_obj, this.type);
            __file_map[fid] = this.id;
        },
        get_item: function (item_value) {
            return $(this.outer + " ul [value='" + item_value + "']");
        },
        del_item: function(item_value) {
            this.get_item(item_value).remove();
            this.files[item_value] = null;
        },
        on_upload_success: function (fid, path_id, path) {
            if (this.files[fid]) {
                this.files[fid].upload = true;
                this.files[fid]['path_id'] = path_id;
                var item = $("#__upload_file_" + fid);
                html = item.html();
                if (this.type === TYPE_JOB_ATTACHMENT_IMG) {
                    $("#__upload_img_" + fid).attr('src', path);
                    item.css({color: 'rgb(45,200,45)'});
                } else {
                    item.html("<a target='_blank' href='" + path + "'>" + html + "</a>");
                }
            }
        },
        on_upload_failed: function (fid) {
            if (this.files[fid]) {
                this.get_item(fid).children('span').css({color: 'red'});
            }
        },
        get_upload_files: function () {
            var ret = [];
            for (var key in this.files) {
                if (this.files.hasOwnProperty(key) && this.files[key]) {
                    ret.push(this.files[key].path_id);
                }
            }
            return ret.length > 0? ret : null;
        },
        clear: function() {
            removeChildren($(this.outer + ' ul'));
            this.files = {};
        },
        files: {}
    };
    registerController(controller_id, controller);

    var accept = '';
    if (controller.type === TYPE_JOB_ATTACHMENT_IMG) {
        accept = 'accept="image/jpeg,image/jpg,image/png,image/bmp"';
    }
    var html = '<div id="' + outer_id + '">';
    html += '<div><a href="javascript:;" class="common_file_input">' + default_param.label;
    html += '<input type="file" ' + accept + ' onchange="onFileSelectorChange(' + controller_id + ')"/></a></div>';
    html += '<div><ul class="' +  default_param.ul_class + '"></ul></div>';
    html += '</div>';
    container.append(html);

    return controller;
}

function onFileSelectorChange(controller_id) {
    __controller_map[controller_id].change();
}

function addAttachmentItem(container, item_data, type) {
    var html = '<li value="' +  item_data.fid + '">';
    html += "<div>";
    html += '<span id="__upload_file_' + item_data.fid + '">' + item_data.name + '</span>';
    html += '<img src="res/images/icon/gray_del.png" onclick="delAttachmentItem(' + item_data.fid + ')" class="common_small_del_btn">';
    html += "</div>";
    if (type === TYPE_JOB_ATTACHMENT_IMG) {
        html += "<div><img class='job_img_attachment' id='__upload_img_" + item_data.fid + "'></div>";
    }
    html += '</li>';
    container.append(html);
}

function delAttachmentItem(fid) {
    getControllerByFid(fid).del_item(fid);
}

function getControllerByFid(fid) {
    return __controller_map[__file_map[fid]];
}

function uploadAttachment(file_obj, type) {
    var reader = new FileReader();
     reader.onload = function (e) {
        file_data = e.target.result;
        $.post("/api/upload_file", {name: file_obj.file.name, file_data: file_data, type: type}, function(data) {
            if (data.status !== 0) {
                promptMsg('上传' + file_obj.file.name + '失败：' + data.msg);
                onFileUploadFailed(file_obj.id);
            } else {
                onFileUploadSuccess(file_obj.id, data.path_id, data.path);
            }
        });
     };
     reader.readAsDataURL(file_obj.file);
}

function onFileUploadSuccess(fid, path_id, path) {
    getControllerByFid(fid).on_upload_success(fid, path_id, path);
}

function onFileUploadFailed(fid) {
    getControllerByFid(fid).on_upload_failed(fid);
}