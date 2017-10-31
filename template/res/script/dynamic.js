
var attachment_controller = null;
var img_attachment_controller = null;

$(document).ready(function () {
    verticalTabs();

    attachment_controller = initAttachmentController($("#attachment_container"));
    img_attachment_controller = initAttachmentController($("#img_attachment_container"), {
        type: TYPE_JOB_ATTACHMENT_IMG,
        label: '添加图片'
    });

    $("#dynamic_send_btn").click(function (event) {
        publishDynamic();
    });

    initCommonWaitingDialog();
    initConfirmDialog();

    initAllDynamic();
    initMyDynamic();
});

function initAllDynamic() {
    commonPost('/api/query_job_list', {query_type: TYPE_JOB_QUERY_DYNAMIC, uid: null}, function (data) {
        var list = '';
        var divider = getDoubleSpace(2);
       data.forEach(function (p1, p2, p3) {
           list += '<div class="all_dynamic_title">' + getDynamicUrlHtml(p1) + '</div>';
           list += '<div class="all_dynamic_info">' + p1.last_operator_name + divider + p1.time + '</div>';
       });
       $("#all_dynamic_list").append(list);
    });
}

function initMyDynamic() {
    commonPost('/api/query_job_list', {query_type: TYPE_JOB_QUERY_DYNAMIC, uid: __my_uid}, function (data) {
        var title = ['主题', '发布时间', '删除'];
        var list = [title];
        data.forEach(function (p1, p2, p3) {
            list.push([
                '<div class="my_dynamic_title">' + getDynamicUrlHtml(p1) + '</div>',
                p1.time,
                '<div class="common_clickable" onclick="delDynamic(' + p1.id + ')">删除</div>'
            ]);
        });
        updateListView($("#my_dynamic_list"), list, {weight: [4,2,1]});
    });
}

function getDynamicUrlHtml(item) {
    var url = 'dynamic_detail.html?job_id=' + item.id;
    return '<a target="_blank" href="' + url + '" title="' + item.title + '">' + item.title + '</a>';
}

function delDynamic(id) {
    showConfirmDialog('确认删除该动态？', function () {
        commonPost("/api/dynamic", {op: 'del', job_id: id}, function (data) {
            promptMsg('删除成功, 1秒后自动刷新');
            setTimeout(function () {
                freshCurrent('my_dynamic_container');
            }, 1000);
        });
    });
}

function publishDynamic() {
    var title = $("#dynamic_topic").val();
    if (!title) {
        promptMsg('主题不能为空');
        return;
    }
    var content = $("#dynamic_content").val();

    var param = {
        op: 'add',
        title: title,
        content: wrapJobContent(content),
        has_attachment: 0,
        has_img: 0,
        type: TYPE_JOB_DYNAMIC
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

    commonPost("/api/dynamic", param, function (data) {
        promptMsg('发布成功, 1秒后自动刷新');
        setTimeout(function () {
            freshCurrent('');
        }, 1000);
    });
}