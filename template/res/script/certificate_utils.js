var desc_salary = {
    title: '收入证明',
    content: "'　　兹证明我司员工{*0:name*}（身份证{*0:id_card*}）在我司任职{*0:position*}，{*2:[税前月薪,税后月薪,税前年薪,税后年薪]*}为{*1:*}元。'"
};

function parseContent(content, info) {
    var tmp = content.replace(/\{\*0:([^\*]*)\*\}/g, "'+'info.$1'+'");
    tmp = eval(tmp);
    tmp.replace(/\{\*1:\*\}/g, "<input type='text'")
}