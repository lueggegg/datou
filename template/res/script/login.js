var OP_FETCH_PSD_BY_QUESTION = 1;
var OP_RESET_PSD = 2;
var OP_RESET_PSD_FROM_ADMIN = 11;

var question_data;

var forget_psd_dlg;
var fetch_psd_by_question_dlg;
var reset_psd_dlg;

var fetch_account;
var fetch_uid;

var account_info_dlg;

$(document).ready(function () {
    document.onkeydown = function (e) {
        if (e.keyCode === 13) {
            $("#login_btn").click();
        }
    };
    $("#login_btn").click(function (event) {
        var account = $("#account").val();
        if (!account) {
            setLoginResultInfo('账号不能为空');
            return;
        }
        var password = $("#password").val();
        if (!password) {
            setLoginResultInfo('密码不能为空');
            return;
        }

        login(account, getHash(password));
    });

     forget_psd_dlg = $("#forget_psd_dialog");
     fetch_psd_by_question_dlg = $("#fetch_psd_by_quetion_dialog");
     reset_psd_dlg = $("#reset_psd_dialog");
     account_info_dlg = $("#account_info_confirm_dlg");
    initDialog(forget_psd_dlg);
    initDialog(fetch_psd_by_question_dlg);
    initDialog(reset_psd_dlg);
    initDialog(account_info_dlg);

    $("#forget_psd").click(function (e) {
        __current_operation = NULL_OPERATION;
        forget_psd_dlg.dialog('open');
    });

    $("#fetch_psd_from_admin").click(function(e) {
        checkFetchAccount(openAccountInfoConfirmDlg);
    });
    
    $("#fetch_psd_by_protect_question").click(function (e) {
        checkFetchAccount(openQuestionDlg);
    });

    initPromptDialog();
});

function login(account, password) {
    $.post('login.html', {account: account, password: password}, function (data) {
        try {
            if (data.status !== 0) {
                setLoginResultInfo('登录错误：' + data.msg);
                return;
            }
            window.location.href = '/index.html';
        } catch (e) {
            console.debug('login exception ' + e);
            redirectError();
        }
    });
}

function setLoginResultInfo(info) {
    $("#login_result").text(info);
}

function initDialog(dialog, width) {
    if (!width) {
        width = 400;
    }
    commonInitDialog(dialog, dealOperation, {width: width});
}

function checkFetchAccount(callback) {
    fetch_account = $("#fetch_account").val();
    if (!fetch_account) {
        promptMsg('请填写账号');
        return;
    }
    commonPost('/api/is_account_exist', {account: fetch_account}, function (data) {
        forget_psd_dlg.dialog('close');
        fetch_uid = data;
        callback();
    });
}

function openAccountInfoConfirmDlg() {
    account_info_dlg.dialog('open');
    __current_operation = OP_RESET_PSD_FROM_ADMIN;
}

function applyResetPsd() {
    var fields = ['name', 'id_card', 'cellphone'];
    var info = {uid: fetch_uid};
    if (fields.some(function (p1, p2, p3) {
        var value = $("#account_info_" + p1).val();
        if (!value) {
            return true;
        }
        info[p1] = value;
        return false;
    })) {
        promptMsg('请完整填写信息');
        return;
    }
    if (!isValidIdCard(info['id_card'])) {
        promptMsg('无效的身份证');
        return;
    }
    if (!isValidPhoneNumber(info['cellphone'])) {
        promptMsg('无效的手机号');
        return;
    }
    commonPost('/api/admin_reset_psd', {op: 'apply', extend: JSON.stringify(info)}, function (data) {
        promptMsg('申请成功，请保持联系方式畅通，管理员审阅后将联系您');
        account_info_dlg.dialog('close');
        fields.forEach(function (p1, p2, p3) {
            $("#account_info_" + p1).val('')
        });
    });
}

function openQuestionDlg() {
    commonPost('/api/get_password_protect_question', {uid: fetch_uid}, function (data) {
        if (!data || data.length === 0) {
            promptMsg('未设置密保问题');
        } else {
            question_data = data;
            question_data.forEach(function (p1, p2, p3) {
                $("#question_" + p2).val(p1.question);
            });
            fetch_psd_by_question_dlg.dialog('open');
            __current_operation = OP_FETCH_PSD_BY_QUESTION;
        }
    });
}

function checkQuestionAnswer() {
    var score = 0;
    question_data.forEach(function (p1, p2, p3) {
        if (p1.answer === $("#answer_" + p2).val()) {
            score++;
        }
    });
    if (score < 2) {
        promptMsg('正确答案少于2个，不能重置密码');
        return;
    }
    fetch_psd_by_question_dlg.dialog('close');
    openResetPsdDlg();
}

function openResetPsdDlg() {
    __current_operation = OP_RESET_PSD;
    reset_psd_dlg.dialog('open');
}

function resetPassword() {
    var new_psd = $("#new_psd").val();
    if (!new_psd) {
        promptMsg('新密码不能为空');
        return;
    }
    var confirm_psd = $("#confirm_psd").val();
    if (new_psd !== confirm_psd) {
        promptMsg('确认密码与新密码不一致');
        return;
    }
    var password = getHash(new_psd);
    commonPost("/api/reset_password", {uid: fetch_uid, password: password}, function (data) {
        login(fetch_account, password);
    });
}

function dealOperation() {
    switch (__current_operation) {
        case OP_FETCH_PSD_BY_QUESTION:
            checkQuestionAnswer();
            break;
        case OP_RESET_PSD:
            resetPassword();
            break;
        case OP_RESET_PSD_FROM_ADMIN:
            applyResetPsd();
            break;
    }
}