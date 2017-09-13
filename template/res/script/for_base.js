
function getGuildItemHtml(item) {
    return '<li><a style="color: white;" href="' + item.href + '">' + item.label + '</a></li>'
}

function showGuildBar() {
    var guild = [
        {href: 'index.html', label: '首页', authority: __common_authority},
        {href: 'personal.html', label: '个人信息', authority: __common_authority},
        {href: 'contact.html', label: '通讯录', authority: __common_authority},
        {href: 'job_record.html', label: '工作流', authority: __common_authority},
        {href: 'official_doc.html', label: '公文交互', authority: __common_authority},
        {href: 'auto_job.html', label: '自动化流程', authority: __common_authority},
        {href: 'company_rule.html', label: '公司制度', authority: __common_authority},
        {href: 'download_file.html', label: '文件下载', authority: __common_authority}
    ];

    var html = '';
    guild.forEach(function (item, p2, p3) {
        if (item.authority >= __authority) {
            html += getGuildItemHtml(item);
        }
    });
    $("#guild_bar").append(html);
}


function baseInit() {
    showGuildBar();
    initPromptDialog();
}

$(function () {
    $("#__common_tag_area").hide();
    baseInit();
});