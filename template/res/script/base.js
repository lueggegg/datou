
var __super_authority = 1;
var __admin_authority = 8;
var __dept_leader_authority = 16;
var __common_authority = 1024;

function redirectError() {
    window.location.href = 'error.html';
}

function getHash(str) {
    return hex_sha1(hex_md5(str));
}

function verticalTabs(target_id) {
    $( target_id ).tabs().addClass( "ui-tabs-vertical ui-helper-clearfix" );
    $( target_id + " li" ).removeClass( "ui-corner-top" ).addClass( "ui-corner-left" )
}

function isValidPhoneNumber(number) {
    return number.length === 11 && parseInt(number)>= 10000000000;
}