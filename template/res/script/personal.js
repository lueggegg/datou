
var info_editors = null;
var editing_info = false;
var psd_questions = null;
var editing_psd_question = [false, false, false];

var custom_info_map = [
    ['#education', 'degree'],
    ['#college', 'college'],
    ['#major', 'major'],
    ['#phone_number', 'cellphone'],
    ['#telephon', 'telephone'],
    ['#email', 'email']
];

OP_NONE = -1;
OP_UPDATE_CUSTOM_INFO = 1;
OP_ALTER_PSD = 2;
OP_ADD_PSD_QUESTION = 11;
OP_UPDATE_PSD_QUESTION = 12;
OP_BIND_PHONE = 21;
OP_CANCEL_BIND_PHONE = 22;
op_current = OP_NONE;

$(document).ready(function () {
    verticalTabs("#tabs");

    info_editors = [$("#education"), $("#college"), $("#major"), $("#phone_number"), $("#telephone"), $("#email")
    ];
    $("#alter_info").click(function (event) {
        if (editing_info) {
            updatePersonalInfo();
        }
        editing_info = !editing_info;
        updateInfoEditorStatus();
        event.preventDefault();
    });

    $("#cancle_alter_info").click(function (event) {
        editing_info = false;
        updateInfoEditorStatus();
        setPersonalCustomInfo();
        event.preventDefault();
    });

    $("#alter_psd_btn").click(function (event) {
        updatePassword();
        event.preventDefault();
    });

    $("#psd_protect_btn").click(function (event) {
        if (!psd_questions) {
            addPsdQuestions();
        }
    });

    $("#update_login_phone_btn").click(function (event) {
        bindPhone();
    });

    $("#cancel_bind_btn").click(function (event) {
        bindPhone(true);
    });

    initPersonalInfo();
    initPsdProtectInfo();
    initPsdQuestionEditBnt(1);
    initPsdQuestionEditBnt(2);
    initPsdQuestionEditBnt(3);
});

function initPersonalInfo() {
    $("#cancle_alter_info").hide();

    $("#account").text(account_info.account);
    $("#user_name").text(account_info.name);
    $("#id_card").text(account_info.id_card);
    $("#user_dept").text(account_info.dept);
    $("#user_role").text(account_info.position);
    $("#join_time").text(account_info.join_date);

    setPersonalCustomInfo();

    $("#personal_portrait").attr('src', account_info.portrait);
}

function setPersonalCustomInfo() {
    $("#education").val(account_info.academic);
    $("#major").val(account_info.major);
    $("#phone_number").val(account_info.phone);
    $("#telephone").val(account_info.telephone);
    $("#email").val(account_info.email);

    custom_info_map.forEach(function (p1, p2, p3) {
        $(p1[0]).val(account_info[p1[1]]);
    });
    if (account_info.login_phone) {
        $("#login_phone").val(account_info.login_phone);
        $("#cancel_bind_btn").show();
    } else {
        $("#cancel_bind_btn").hide();
    }
}

function initPsdProtectInfo() {
    $.post('/api/get_password_protect_question', {uid: account_info.id}, function (data) {
        try {
            if (data.status !== 0) {
                redirectError();
                return;
            }
            psd_questions = data.data;
            if (psd_questions) {
                setPsdProtectInfo();
            } else {
                $("#edit_psd_question_1").hide();
                $("#edit_psd_question_2").hide();
                $("#edit_psd_question_3").hide();
            }
            $("#cancel_edit_psd_question_1").hide();
            $("#cancel_edit_psd_question_2").hide();
            $("#cancel_edit_psd_question_3").hide();
        } catch (e) {
            console.debug('get psd question: ' + e);
            redirectError();
        }
    })
}

function setPsdProtectInfo() {
    psd_questions.forEach(function (p1, p2, p3) {
        question_container = $("#psd_question_" + (p2+1));
        question_container.val(p1.question);
        question_container[0].disabled = true;
        $("#psd_answer_" +  (p2+1) + "_container").hide();
    });
    $("#psd_protect_btn_container").hide();
}

function initPsdQuestionEditBnt(index) {
    var question_editor = $("#psd_question_" + index);
    var answer_editor = $("#psd_answer_" + index);
    var answer_container = $("#psd_answer_" + index + "_container");
    var cancel_btn = $("#cancel_edit_psd_question_" + index);
    $("#edit_psd_question_" + index).click(function (event) {
        var editing = !editing_psd_question[index - 1];
        if (editing) {
            if (!canEditPsdQuestion()) {
                setPsdProtectResult('请完成其他编辑项');
                return;
            }
            editing_psd_question[index - 1] = editing;
            $(this).text('保存');
            cancel_btn.show();
            question_editor[0].disabled = false;
            answer_editor.val('');
            answer_container.show();
        } else {
            var question = question_editor.val();
            var answer = answer_editor.val();
            if (!(question && answer)) {
                setPsdProtectResult('问题或答案不能为空');
                return;
            }
            if (psd_questions.some(function (p1, p2, p3) {
                    if (p2 !== index - 1) {
                        if (p1.question === question) {
                            setPsdProtectResult('请设置互不相同的密保问题');
                            return true;
                        }
                    }
                })) {
                return;
            }
            editing_psd_question[index - 1] = editing;
            $(this).text('编辑');
            cancel_btn.hide();
            question_editor[0].disabled = true;
            answer_container.hide();
            updatePsdQuestions(index-1, question, answer);
        }
    });
    cancel_btn.click(function (event) {
        editing_psd_question[index - 1] = false;
        $("#edit_psd_question_" + index).text('编辑');
        $(this).hide();
        question_editor.val(psd_questions['psd_question_' + index]);
        question_editor[0].disabled = true;
        answer_container.hide();
    });
}

function canEditPsdQuestion() {
    return !(editing_psd_question[0] || editing_psd_question[1] || editing_psd_question[2]);
}

function updateInfoEditorStatus() {
    info_editors.forEach(function (p1, p2, p3) {
        p1[0].disabled = !editing_info;
    });
    $("#alter_info").text(editing_info? '保存' : '编辑');
    if (editing_info) {
        $("#cancle_alter_info").show();
    } else {
        $("#cancle_alter_info").hide();
    }
}

function updatePersonalInfo() {
    var info = {};

    custom_info_map.forEach(function (p1, p2, p3) {
       var item = $(p1[0]).val();
       if (item !== account_info[p1[1]]) info[p1[1]] = item;
    });

    op_current = OP_UPDATE_CUSTOM_INFO;
    $.post('/api/alter_account', {op: 'update', uid: account_info.id, account_info: JSON.stringify(info)}, operationResult);
}

function updatePassword() {
    var old_psd = $("#original_psd").val();
    if (!old_psd) {
        setAlterPasswordResult('原密码不能为空');
        return;
    }
    var new_psd = $("#new_psd").val();
    if (!new_psd) {
        setAlterPasswordResult('新密码不能为空');
        return;
    }
    var confirm_psd = $("#confirm_psd").val();
    if (!confirm_psd) {
        setAlterPasswordResult('确认密码不能为空');
        return;
    }
    if (new_psd !== confirm_psd) {
        setAlterPasswordResult('确认密码与新密码不同');
        return;
    }
    old_psd = getHash(old_psd);
    if (old_psd !== account_info.password) {
        setAlterPasswordResult('原密码错误');
        return;
    }

    var info = {password: getHash(new_psd)};
    op_current = OP_ALTER_PSD;
    $.post('/api/alter_account', {op: 'update', uid: account_info.id, account_info: JSON.stringify(info)}, operationResult);
}

function setAlterPasswordResult(msg) {
    setResultMsg($("#alter_psd_result"), msg);
}

function addPsdQuestions() {
    var question_1 = $("#psd_question_1").val();
    var answer_1 = $("#psd_answer_1").val();
    var question_2 = $("#psd_question_2").val();
    var answer_2 = $("#psd_answer_2").val();
    var question_3 = $("#psd_question_3").val();
    var answer_3 = $("#psd_answer_3").val();
    if (!(question_1 && question_2 && question_3 && answer_1 && answer_2 && answer_3)) {
        setPsdProtectResult('请填写完所有密码保护问题与答案');
        return;
    }
    if (question_1 === question_2 || question_1 === question_3 || question_2 === question_3) {
        setPsdProtectResult('请设置互不相同的密保问题');
        return;
    }
    psd_questions = [[], [], []];
    psd_questions[0].push(question_1);
    psd_questions[0].push(answer_1);
    psd_questions[1].push(question_2);
    psd_questions[1].push(answer_2);
    psd_questions[2].push(question_3);
    psd_questions[2].push(answer_3);
    op_current = OP_ADD_PSD_QUESTION;
    $.post('/api/update_password_protect_question', {op: 'add', question_info: JSON.stringify(psd_questions)}, operationResult);
}

function updatePsdQuestions(index, question, answer) {
    psd_questions[index][0] = question;
    psd_questions[index][1] = answer;
    var data = {};
    data['question'] = question;
    data['answer'] = answer;
    op_current = OP_UPDATE_PSD_QUESTION;
    $.post('/api/update_password_protect_question',
        {op: 'update', question_id: psd_questions[index].id, question_info: JSON.stringify(data)}, operationResult);
}

function setPsdProtectResult(msg) {
    setResultMsg($("#psd_protect_result"), msg);
}

function bindPhone(cancel) {
    cancel = !!cancel;
    var phone = null;
    if (cancel) {
        op_current = OP_CANCEL_BIND_PHONE;
    } else {
        op_current = OP_BIND_PHONE;
        phone = $("#login_phone").val();
        if (!phone) {
            setBindPhoneResult('手机号码不能为空');
            return;
        }
        if (!isValidPhoneNumber(phone)) {
            setBindPhoneResult('无效的手机号码');
            return;
        }
    }
    var password = $("#login_password").val();
    if (!password) {
        setBindPhoneResult('登录密码不能为空');
        return;
    }
    if (getHash(password) !== account_info['password']) {
        setBindPhoneResult('登录密码错误');
        return;
    }
    $("#login_password").val('');
    var info = {login_phone: phone};
    $.post('/api/alter_account', {op: 'update', uid: account_info.id, account_info: JSON.stringify(info)}, operationResult);
}

function setBindPhoneResult(msg) {
    setResultMsg($("#update_login_phone_result"), msg);
}

function setResultMsg(container, msg) {
    container.text(msg);
    setTimeout(function () {
        container.text(' ');
    }, 5000);
}

function operationResult(data) {
    try {
        if (data.status !== 0) {
            promptMsg(data.msg);
            return;
        }
        if (op_current === OP_ALTER_PSD) {
            window.location.href = 'logout.html';
        } else if (op_current === OP_ADD_PSD_QUESTION) {
            // setPsdProtectInfo();
            // $("#edit_psd_question_1").show();
            // $("#edit_psd_question_2").show();
            // $("#edit_psd_question_3").show();
            freshCurrent('password_protect');
        } else if (op_current === OP_BIND_PHONE) {
            setBindPhoneResult('绑定成功');
            $("#cancel_bind_btn").show();
        } else if (op_current === OP_CANCEL_BIND_PHONE) {
            account_info.login_phone = '';
            $("#login_phone").val('');
            setBindPhoneResult('解除绑定成功');
            $("#cancel_bind_btn").hide();
        }
    } catch (e) {
        redirectError();
    }
}