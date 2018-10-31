//(function () {
//    'use strict';
//
//    var website = openerp.website;
//    var _t = openerp._t;
//    var webEditor = website.editor;
//
//    console.log('website_forum_imagedialog');
//
//    website.RTE.include({
//        events: {
//            'click .cke_button_icon.cke_button__image_icon': 'testImg',
//        },
//
//        init: function (EditorBar) {
//            this.EditorBar = EditorBar;
//            this._super.apply(this, arguments);
//        },
//
//        testImg: function () {
//            console.log('testImg');
//            console.log(this);
//
//        },
//    });
//})();

openerp.website.if_dom_contains('.cke_1.cke.cke_reset.cke_chrome.cke_editor_content.cke_ltr.cke_browser_webkit', function () {
    console.log('test');
    console.log(openerp.website.RTE._config);
    $('.cke_button_icon.cke_button__image_icon').on('click', function(e) {
        console.log('imagedialog');
//        console.log(e);
        var test = $('.cke_dialog_body');
        console.log(test)
//        $('<div>test</div>').insertBefore('.cke_dialog_body');
        $('.cke_dialog_body').remove();
        console.log(openerp.website.RTE._config);

    });

});
