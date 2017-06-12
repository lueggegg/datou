
var news_imgs = [
    'res/images/a.jpg',
    'res/images/b.jpg',
    'res/images/c.jpg'
];
var current_img_index = 0;
var img_size = news_imgs.length;

$(document).ready(function () {
    looperNewImg(2000);
});

function looperNewImg(millis) {
    setTimeout(function () {
        current_img_index++;
        if (current_img_index === img_size) {
            current_img_index = 0;
        }
        $("#index_big_img").attr('src', news_imgs[current_img_index]);
        looperNewImg(millis);
    }, millis);
}