var job_container = [];
var job_types = [];

$(document).ready(function () {
    verticalTabs();

    job_container.push(
        $("#job_waiting"),
        $("#job_processed"),
        $("#job_completed"),
        $("#job_sent_by_myself")
    );
    job_types.push(
        STATUS_JOB_MARK_WAITING,
        STATUS_JOB_MARK_PROCESSED,
        STATUS_JOB_MARK_COMPLETED,
        STATUS_JOB_INVOKED_BY_MYSELF
    );

    for (var i in job_types) {
        queryJobList(i);
    }
});

function queryJobList(index) {
    var param = {
        status: job_types[index]
    };
    commonPost('/api/query_job_list', param, function (data) {
        setJobData(index, data);
    });
}

function setJobData(index, data) {
    if (index < 4) {
        var weight =[1.2, 2, 1, 1.5, 1.5, 1.5];
        var title = ['类型', '主题', '发送人', '发送时间', '上一个审阅人', '最后操作时间'];
        var new_status = job_types[index] === STATUS_JOB_MARK_COMPLETED
            || job_types[index] === STATUS_JOB_INVOKED_BY_MYSELF;
        var status = {};
        if (new_status) {
            title.push('状态');
            weight.push(1);
            status[STATUS_JOB_PROCESSING] = '<span style="color: orange">处理中</span>';
            status[STATUS_JOB_COMPLETED] = '<span style="color: rgb(0,225,32)">已完成</span>';
            status[STATUS_JOB_REJECTED] = '<span style="color: red">未通过</span>';
            status[STATUS_JOB_CANCEL] = '<span style="color: gray">已撤回</span>';
        }
        var list_data = [title];
        data.forEach(function (p1, p2, p3) {
            var item = [
                '<span style="color: orange">[' + job_type_map[p1.type] + ']</span>',
                "<div class=common_clickable onclick='onClickDocItem(" + p1.type + "," + p1.id + ")'>" + p1.title + "</div>",
                "<div>" + p1.invoker_name + "</div>",
                abstractDateFromDatetime(p1.time),
                commonGetString(p1.last_operator_name),
                abstractDateFromDatetime(p1.mod_time)
            ];
            if (new_status) {
                item.push(status[p1.job_status]);
            }

            list_data.push(item);
        });
        updateListView(job_container[index], list_data, {weight: weight});
    }
}

function onClickDocItem(job_type, job_id) {
    switch (job_type) {
        case TYPE_JOB_OFFICIAL_DOC:
            window.open('/doc_detail.html?job_id=' + job_id, '公文详情');
            break;
        default:
            window.open('/auto_job_detail.html?job_id=' + job_id + "&title=" + job_type_map[job_type], '自动化流程');
            break;
    }
}