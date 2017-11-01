var __controller_index = 0;

function createPageController (container, items_per_page, callback, cb_args) {
    var controller = {
        container: container,
        items_per_page: items_per_page,
        current_page: 0,
        total_page: 0,
        total_count: 0,
        callback: callback,
        cb_args: cb_args,
        pre_btn: null,
        next_btn: null,
        index_view: null,
        spinner: null,
        goto_btn: null,

        getOffset: function () {
            return (this.items_per_page) * this.current_page;
        },

        updateView: function () {
            // this.pre_btn[0].disabled = this.current_page === 0;
            // this.next_btn[0].disabled = this.current_page === this.total_page - 1;
            this.index_view.text('第' + (this.current_page + 1) + '页（共' + this.total_page + "页, " + this.total_count + "条）");
            this.spinner.spinner('value', this.current_page + 1);
        },

        response: function (event) {
            this.callback(this.getOffset(), this.items_per_page, this.cb_args);
            this.updateView();
            event.preventDefault();
        },

        reset: function (total_count) {
            this.total_count = total_count;
            this.total_page = Math.ceil(total_count/items_per_page);
            this.current_page = 0;
            this.updateView();
            if (this.total_page > 1) {
                this.container.show();
            } else {
                this.container.hide();
            }
        },

        updateTotalCount: function (total_count) {
            if (this.total_count === total_count) {
                return;
            }
            this.total_count = total_count;
            this.total_page = Math.ceil(total_count/items_per_page);
            if (this.current_page > this.total_page) {
                this.current_page = this.total_page;
            }
            this.updateView();
            if (this.total_page > 1) {
                this.container.show();
            } else {
                this.container.hide();
            }
        }
    };

    container.append(getPageControllerHtml());
    controller.pre_btn = $("#" + getCurrentViewId('pre_btn'));
    controller.next_btn = $("#" + getCurrentViewId('next_btn'));
    controller.index_view = $("#" + getCurrentViewId('index'));
    controller.spinner = $("#" + getCurrentViewId('spinner'));
    controller.spinner.spinner( {
        spin: function( event, ui ) {
            if (ui.value < 1) {
                $(this).spinner("value", controller.total_page);
                return false;
            } else if (ui.value > controller.total_page) {
                $(this).spinner("value", 1);
                return false;
            }
        }
    });
    controller.pre_btn.click(function (event) {
        if (controller.current_page > 0) {
            controller.current_page--;
            controller.response(event);
        }
    });

    controller.next_btn.click(function (event) {
        if (controller.current_page < controller.total_page - 1) {
            controller.current_page++;
            controller.response(event);
        }
    });
    $("#" + getCurrentViewId('goto_btn')).click( function (event) {
        var page = controller.spinner.val();
        if (!isNaN(page)) page = 1;
        page = Math.floor(page);
        if (page < 1) page = 1;
        else if (page > controller.total_page) page = controller.total_page;
        controller.current_page = page - 1;
        controller.response(event);
    });
    container.addClass('page_controller_container');
    container.hide();
    __controller_index++;

    return controller;
}

function getPageControllerHtml() {
    var html = '<ul class="page_controller">';
    html += "<li title='上一页' style='width: 10%;' class='common_clickable' id='" + getCurrentViewId('pre_btn') + "'><<</li>";
    html += "<li style='width: 40%;' id='" + getCurrentViewId('index') + "'>第1页</li>";
    html += "<li title='下一页' style='width: 10%;' class='common_clickable' id='" + getCurrentViewId('next_btn') + "'>>></li>";
    html += "<li style='width: 38%;'>";
    html += "<div class='element_left page_controller_spinner_container'><input class='page_controller_spinner' id='" + getCurrentViewId("spinner") + "'></div>";
    html += "<div class='element_left'><button class='ui-button ui-corner-all' id='" + getCurrentViewId("goto_btn") + "'>转到</button></div>";
    html += "</li>";
    html += '</ul>';
    return html;
}

function getCurrentViewId(view) {
    return "__" + view + "_page_controller_" +  __controller_index;
}
