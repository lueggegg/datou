var NULL_OPERATION = -1;
var OP_FETCH_PSD_BY_QUESTION = 1;
var OP_RESET_PSD = 2;
var current_operation = NULL_OPERATION;

var question_data;

var forget_psd_dlg;
var fetch_psd_by_question_dlg;
var reset_psd_dlg;

var fetch_account;
var fetch_uid;

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
    initDialog(forget_psd_dlg);
    initDialog(fetch_psd_by_question_dlg);
    initDialog(reset_psd_dlg);

    $("#forget_psd").click(function (e) {
        current_operation = NULL_OPERATION;
        forget_psd_dlg.dialog('open');
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
    dialog.dialog({
        autoOpen: false,
        modal: true,
        width: width,
        buttons: [
            {
                text: "确定",
                click: function() {
                    if (current_operation === NULL_OPERATION) {
                        $( this ).dialog( "close" );
                        return;
                    }
                    dealOperation();
                }
            },
            {
                text: "返回",
                click: function() {
                    $( this ).dialog( "close" );
                }
            }
        ]
    });
}

function checkFetchAccount(callback) {
    fetch_account = $("#fetch_account").val();
    if (!fetch_account) {
        promptMsg('请填写账号');
        return;
    }
    $.post('/api/is_account_exist', {account: fetch_account}, function (data) {
        try {
            if (data.status !== 0) {
                promptMsg(data.msg);
            } else {
                forget_psd_dlg.dialog('close');
                fetch_uid = data.data;
                callback();
            }
        } catch (e) {
            redirectError(e);
        }
    });
}

function openQuestionDlg() {
    $.post('/api/get_password_protect_question', {uid: fetch_uid}, function (data) {
        try {
            if (data.status !== 0) {
                promptMsg(data.msg);
                return;
            }
            if (!data.data || data.data.length === 0) {
                promptMsg('未设置密保问题');
            } else {
                question_data = data.data;
                question_data.forEach(function (p1, p2, p3) {
                    $("#question_" + p2).val(p1.question);
                });
                fetch_psd_by_question_dlg.dialog('open');
                current_operation = OP_FETCH_PSD_BY_QUESTION;
            }
        } catch (e) {
            redirectError(e);
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
    current_operation = OP_RESET_PSD;
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
    $.post("/api/reset_password", {uid: fetch_uid, password: password}, function (data) {
        try {
            if (data.status !== 0) {
                promptMsg(data.msg);
            } else {
                login(fetch_account, password);
            }
        } catch (e) {
            redirectError(e);
        }
    })
}

function dealOperation() {
    switch (current_operation) {
        case OP_FETCH_PSD_BY_QUESTION:
            checkQuestionAnswer();
            break;
        case OP_RESET_PSD:
            resetPassword();
            break;
    }
}