var OP_ADD_NEWS_LINK = 1;
var OP_UPDATE_NEWS_LINK = 2;
var OP_DEL_NEWS_LINK = 3;

var news_config_dlg = null;
var current_news_type;
var link_data_map = {};
var current_operating_news;

$(document).ready(function () {

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

        var title = ['标题', '预览', '删除'];
        var list_data = [title];
        data.forEach(function (p1, p2, p3) {
            list_data.push([
                getNewsItemOperationHtml(p1.title, type, p2, OP_UPDATE_NEWS_LINK),
                "<a target='_blank' href='" + p1.url + "'>预览</a>",
                getNewsItemOperationHtml('删除', type, p2, OP_DEL_NEWS_LINK)
            ]);
        });
        updateListView(link_data_map[type].list_container, list_data, {weight: [4,1,1]})
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
                commonPost('/api/outer_link', {op: 'del', link_id: link_data_map[type].news_data[index].id}, onResult)
            });
            break;
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
        var img_url = $("#editor_img_url").val();
        if (!img_url) {
            promptMsg('请输入图片链接');
            return;
        }
        param['img_url'] = img_url;
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
        var img_url = $("#editor_img_url").val();
        if (!img_url) {
            promptMsg('请输入图片链接');
            return;
        }
        param['img_url'] = img_url;
    }

    commonPost('/api/outer_link', param, function (data) {
        link_data_map[current_news_type].news_data.some(function (p1, p2, p3) {
            if (p1.id === current_operating_news) {
                p1.title = title;
                p1.url = url;
                if (current_news_type === TYPE_NEWS_LINK_IMG) {
                    p1.img_url = param.img_url;
                }
                return true;
            }
        });
        news_config_dlg.dialog('close');
        promptMsg('更新成功');
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
            freshCurrent(link_data_map[current_news_type].anchor);
            break;
    }
}