(function () {
    'use strict';

    // Overwrite class method of website/static/src/js/website.editor.js@839
    // to append/set/override CKEDITOR.config for wrapwrap editor
    openerp.website.RTE = openerp.website.RTE.extend({

        _config: function () {
            // Run the original method to modify it's result
            var config =  this._super();

            // Custom editor skin
            // https://ckeditor.com/cke4/addons/skins/all?page=1
            // https://stackoverflow.com/questions/39998300/ckeditor-set-custom-skinpath
            // config.skin = 'moono,/web/static/lib/ckeditor/skins/moono/';
            // config.skin = 'minimalist,/fso_website_email/static/src/lib/ckeditor/skins/minimalist/';
            config.skin = 'moono-lisa,/fso_website_email/static/src/lib/ckeditor/skins/moono-lisa/';

            // Enable Paste As Plain Text
            config.forcePasteAsPlainText = true;

            // Add Custom font and font background colors
            config.colorButton_colors = 'CF5D4E,454545';

            // Set custom toolbar
            // https://docs.ckeditor.com/ckeditor4/latest/guide/dev_toolbar.html
            config.toolbar = [{
                name: 'basicstyles', items: [
                    "Bold", "Italic", "Underline", "Strike", "Subscript",
                    "Superscript", "RemoveFormat"
                ]
            }, {
                name: 'span', items: [
                    "Link", "Blockquote", "BulletedList",
                    "NumberedList", "Indent", "Outdent"
                ]
            }, {
                name: 'justify', items: [
                    "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"
                ]
            }, {
                name: 'special', items: [
                    "Image"
                ]
            }, {
                name: 'styles', items: [
                    "Styles"
                ]
            }
            ];

            // // Set custom styles for the styles drop down
            // // https://docs.ckeditor.com/ckeditor4/latest/guide/dev_howtos_styles.html
            // config.stylesSet = [
            //         {name: "Normal", element: 'p'},
            //         {name: "Heading 1", element: 'h1'}
            //     ];

            // return the config
            return config;
        }

    });


})();
