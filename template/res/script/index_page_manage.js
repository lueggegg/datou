var OP_ADD_NEWS_LINK = 1;
var OP_UPDATE_NEWS_LINK = 2;
var OP_DEL_NEWS_LINK = 3;
var OP_TOP_NEWS_LINK = 4;

var news_config_dlg = null;
var current_news_type;
var link_data_map = {};
var current_operating_news;

var local_img_data;
var local_img_path;

$(document).ready(function () {
    needAuthority(OPERATION_MASK_INDEX_PAGE);

    news_config_dlg = $("#news_config_dlg");
    commonInitDialog(news_config_dlg, dealOperation, {width: 600});

    var link_type = [
        [TYPE_NEWS_LINK_IMG, 'img_news_link', '图片新闻'],
        [TYPE_NEWS_LINK_COMPANY, 'company_news_link', '公司新闻'],
        [TYPE_NEWS_LINK_OTHER, 'other_news_link', '其他资讯'],
        [TYPE_USEFUL_LINK, 'useful_link', '常用链接']
    ];
    link_type.forEach(function (p1, p2, p3) {
        $("#tab_item_list").append("<li><a href='#" + p1[1] + "'>" + p1[2] + "</a></li>");
        var item = "<div id='" + p1[1] + "'>";
        item += "<div class='common_btn_container'>";
        item += "<button onclick='openNewsLinkDlg(" + p1[0] + ")' class='ui-button ui-corner-all element_right'>增加链接</button>";
        item += "</div>";
        item += "<div><ul id='" + p1[1] + "_list'></ul></div>";
        item += "</div>";
        $("#tabs").append(item);
        link_data_map[p1[0]] = {
            title: p1[2],
            news_data: null,
            list_container: $("#" + p1[1] + "_list"),
            anchor: p1[1]
        };
        queryNewsLink(p1[0]);
    });
    verticalTabs();

    $("#img_type").checkboxradio();
    $("#local_img_container").hide();
    $("#upload_img_btn").hide();

    initConfirmDialog();
});

function dealOperation() {
    switch (__current_operation) {
        case OP_ADD_NEWS_LINK:
            addNewsLink();
            break;
        case OP_UPDATE_NEWS_LINK:
            updateNewsLink();
            break;
    }
}

function queryNewsLink(type) {
    commonPost('/api/outer_link', {op: 'query', type: type}, function (data) {
        link_data_map[type].news_data = data;

        var title = ['标题', '预览', '置顶', '删除'];
        var list_data = [title];
        data.forEach(function (p1, p2, p3) {
            list_data.push([
                getNewsItemOperationHtml(p1.title, type, p2, OP_UPDATE_NEWS_LINK),
                "<a id='item_view_url_'" + p1.id + "' target='_blank' href='" + p1.url + "'>预览</a>",
                getNewsItemOperationHtml('置顶', type, p2, OP_TOP_NEWS_LINK),
                getNewsItemOperationHtml('删除', type, p2, OP_DEL_NEWS_LINK)
            ]);
        });
        updateListView(link_data_map[type].list_container, list_data, {weight: [4,1,1,1]})
    });
}

function getNewsItemOperationHtml(label, type, index, operation) {
    var arg = type + ',' + index + ',' + operation;
    return "<div title='" + label + "' class='common_clickable' onclick='onNewsItemOperation(" + arg + ")'>" + label + "</div>";
}

function onNewsItemOperation(type, index, operation) {
    __current_operation = operation;
    switch (operation) {
        case OP_UPDATE_NEWS_LINK:
            openNewsLinkDlg(type, link_data_map[type].news_data[index]);
            break;
        case OP_DEL_NEWS_LINK:
            showConfirmDialog('确认删除链接？', function () {
                current_news_type = type;
                commonPost('/api/outer_link', {op: 'del', link_id: link_data_map[type].news_data[index].id}, onResult);
            });
            break;
        case OP_TOP_NEWS_LINK:
            current_news_type = type;
            commonPost('/api/outer_link', {op: 'top', link_id: link_data_map[type].news_data[index].id}, onResult);
    }
}

function openNewsLinkDlg(type, data) {
    current_news_type = type;
    if (data) {
        current_operating_news = data.id;
        $("#editor_news_title").val(data.title);
        $("#editor_news_url").val(data.url);
        __current_operation = OP_UPDATE_NEWS_LINK;
        news_config_dlg.dialog('option', 'title', '修改' + link_data_map[type].title);
    } else {
        current_operating_news = null;
        $("#editor_news_title").val('');
        $("#editor_news_url").val('');
        __current_operation = OP_ADD_NEWS_LINK;
        news_config_dlg.dialog('option', 'title', '增加' + link_data_map[type].title);
    }
    if (type === TYPE_NEWS_LINK_IMG) {
        var img_url = data? data.img_url : '';
        $("#editor_img_url").val(img_url);
        $("#dlg_img").attr('src', img_url);
        $("#dlg_img_container").show();
        $("#img_type").attr('checked', false);
        $("#img_type").checkboxradio('refresh');
        $("#upload_img_btn").hide();
        changeImgContainer(false);
        local_img_path = null;
    } else {
        $("#dlg_img_container").hide();
    }
    news_config_dlg.dialog('open');
}

function addNewsLink() {
    var title = $("#editor_news_title").val();
    if (!title) {
        promptMsg('请输入标题');
        return;
    }
    var url = $("#editor_news_url").val();
    if (!url) {
        promptMsg('请输入网页链接');
        return;
    }

    var param = {
        op: 'add',
        type: current_news_type,
        title: title,
        url: url
    };

    if (current_news_type === TYPE_NEWS_LINK_IMG) {
        var checked = $("#img_type").is(":checked");
        if (checked) {
            if (!local_img_path) {
                promptMsg('请上传本地图片');
                return;
            }
            param['img_url'] = local_img_path;
        } else {
            var img_url = $("#editor_img_url").val();
            if (!img_url) {
                promptMsg('请输入图片链接');
                return;
            }
            param['img_url'] = img_url;
        }
    }

    commonPost('/api/outer_link', param, onResult);
}

function updateNewsLink() {
    var title = $("#editor_news_title").val();
    if (!title) {
        promptMsg('请输入标题');
        return;
    }
    var url = $("#editor_news_url").val();
    if (!url) {
        promptMsg('请输入网页链接');
        return;
    }

    var param = {
        op: 'update',
        link_id: current_operating_news,
        type: current_news_type,
        title: title,
        url: url
    };

    if (current_news_type === TYPE_NEWS_LINK_IMG) {
        var checked = $("#img_type").is(":checked");
        if (checked) {
            if (!local_img_path) {
                promptMsg('请上传本地图片');
                return;
            }
            param['img_url'] = local_img_path;
        } else {
            var img_url = $("#editor_img_url").val();
            if (!img_url) {
                promptMsg('请输入图片链接');
                return;
            }
            param['img_url'] = img_url;
        }
    }

    commonPost('/api/outer_link', param, function (data) {
        link_data_map[current_news_type].news_data.some(function (p1, p2, p3) {
            if (p1.id === current_operating_news) {
                $("#item_view_url_" + current_operating_news).attr('href', url);
                p1.title = title;
                p1.url = url;
                if (current_news_type === TYPE_NEWS_LINK_IMG) {
                    p1.img_url = param.img_url;
                }
                return true;
            }
        });
        news_config_dlg.dialog('close');
        onResult(data);
    });
}

function viewImgUrl() {
    $("#dlg_img").attr('src', $("#editor_img_url").val());
}

function viewLink() {
    window.open($("#editor_news_url").val());
}

function onResult(data) {
    switch (__current_operation) {
        case OP_ADD_NEWS_LINK:
        case OP_DEL_NEWS_LINK:
        default:
            freshCurrent(link_data_map[current_news_type].anchor);
            break;
    }
}

function onImgFileSelectorChanged() {
    var files = $("#img_file")[0].files;
    if (files.length === 0) {
        return;
    }
    var f = files[0];
    var reader = new FileReader();
    reader.onload = function (e) {
        local_img_data = e.target.result;
        $("#dlg_img").attr('src', local_img_data);
        $("#upload_img_btn").show();
        $("#img_file").val('');
    };
    reader.readAsDataURL(f);
}

function uploadImg() {
    if (!local_img_data) {
        promptMsg('未选择图片');
        return;
    }
    commonPost('/api/upload_file', {type: TYPE_UPLOAD_COMMON_IMG, name: 'null', file_data: local_img_data}, function (data) {
        local_img_path = data.path;
        promptMsg('上传成功');
    });
}

function onImgTypeChanged() {
    var checked = $("#img_type").is(":checked");
    changeImgContainer(checked);
}

function changeImgContainer(checked) {
    if (checked) {
        $("#img_url_container").hide();
        $("#local_img_container").show();
    } else {
        $("#img_url_container").show();
        $("#local_img_container").hide();
    }
}