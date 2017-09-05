
$(document).ready(function () {
    $("#inline_date").datepicker();

    queryImgNews();
    queryTextNews();
    queryUsefulLink();
    queryRecentJob();
});

var img_news = null;
var current_img_index = 0;
var img_size = 0;

function queryImgNews() {
    commonPost('/api/outer_link', {op: 'query', type: TYPE_NEWS_LINK_IMG}, function (data) {
        img_news = data;
        img_size = img_news.length;
        if (img_size !== 0) {
            showCurrentImgNews();
        }
        if (img_size > 1) {
            looperNewImg(3000);
        }
    });
}

function queryTextNews() {
    [
        [TYPE_NEWS_LINK_COMPANY, $("#company_news_list")],
        [TYPE_NEWS_LINK_OTHER, $("#other_news_list")]
    ].forEach(function (p1, p2, p3) {
        commonPost('/api/outer_link', {op: 'query', type: p1[0], count: 5}, function (data) {
            if (data.length === 0) {
                p1[1].append('<li>没有要闻</li>');
            } else {
                var list = '';
                data.forEach(function (item, index, p) {
                    list += "<li><a target='_blank' title='" + item.title + "' href='" + item.url +"'>" + item.title + "</a></li>";
                });
                p1[1].append(list);
            }
        })
    });
}

function queryUsefulLink() {
    commonPost('/api/outer_link', {op: 'query', type: TYPE_USEFUL_LINK}, function (data) {
        if (data.length > 0) {
            var html = "<div class='index_news_divider'></div><div class='topic_title'>常用链接</div>";
            html += "<ul class='base_ul'>";
            data.forEach(function (item, p2, p3) {
                html += "<li><a target='_blank' title='" + item.title + "' href='" + item.url +"'>" + item.title + "</a></li>";
            });
            html += "</ul>";
            $("#useful_link_container").append(html);
        }
    });
}

function looperNewImg(millis) {
    setTimeout(function () {
        current_img_index++;
        if (current_img_index === img_size) {
            current_img_index = 0;
        }
        showCurrentImgNews();
        looperNewImg(millis);
    }, millis);
}

function showCurrentImgNews() {
    var item = img_news[current_img_index];
    $("#img_news_img").attr('src', item.img_url);
    $("#img_news_title").text(item.title);
    $("#img_news_url").attr('href', item.url);
    $("#img_news_url").attr('title', item.title);
}

function queryRecentJob() {
    commonPost('/api/query_job_list', {count: 10}, function (data) {
        if (data.length === 0) {

        } else {
            $("#empty_job_container").hide();
            var job_status = {};
            job_status[STATUS_JOB_PROCESSING] = '<span style="color: orange">处理中</span>';
            job_status[STATUS_JOB_COMPLETED] = '<span style="color: rgb(0,225,32)">已完成</span>';
            job_status[STATUS_JOB_REJECTED] = '<span style="color: red">未通过</span>';
            job_status[STATUS_JOB_CANCEL] = '<span style="color: gray">被撤回</span>';
            var mark_status = {};
            mark_status[STATUS_JOB_MARK_COMPLETED] = '已归档';
            mark_status[STATUS_JOB_MARK_WAITING] = '待办';
            mark_status[STATUS_JOB_MARK_PROCESSED] = '已处理';
            var list = '';
            data.forEach(function (p1, p2, p3) {
                list += '<ul class="recent_info_item">';
                list += '<li class="recent_info_type">[' + job_type_map[p1.type] + ']</li>';
                list += '<li class="recent_info_mark_status">' + mark_status[p1.mark_status] + '</li>';
                list += '<li class="recent_info_status">' + job_status[p1.job_status] + '</li>';
                list += '<li class="recent_info_main"><div><a target="_blank" href="'
                    + getRecentJobUrl(p1.type, p1.job_id) + '" title="' + p1.title + '">' + p1.title + "</a></div></li>";
                list += '</ul>';
            });
            $("#recent_job_list").append('<li>' + list + '</li>');
        }
    });
}

function getRecentJobUrl(job_type, job_id) {
    switch (job_type) {
        case TYPE_JOB_OFFICIAL_DOC:
            return 'doc_detail.html?job_id=' + job_id;
        default:
            return 'auto_job_detail.html?job_id=' + job_id + "&title=" + job_type_map[job_type];
    }
}