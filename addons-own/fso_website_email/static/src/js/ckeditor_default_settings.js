(function () {
    'use strict';

    // Overwrite class method of website/static/src/js/website.editor.js@839
    // to append/set/override CKEDITOR.config for wrapwrap editor
    openerp.website.RTE.include({

        _config: function () {
            // console.log('Custom config for CK-Editor for email templates with BRANGEL addon :)')
            // Run the original method to modify it's result
            var config = this._super();

            // Custom editor skin
            // https://ckeditor.com/cke4/addons/skins/all?page=1
            // https://stackoverflow.com/questions/39998300/ckeditor-set-custom-skinpath
            // config.skin = 'moono,/web/static/lib/ckeditor/skins/moono/';
            // config.skin = 'minimalist,/fso_website_email/static/src/lib/ckeditor/skins/minimalist/';
            config.skin = 'moono-lisa,/fso_website_email/static/src/lib/ckeditor/skins/moono-lisa/';

            // Filler text (non-breaking space entity — &nbsp;) will be inserted into empty block elements
            config.fillEmptyBlocks = true;

            // ATTENTION: Can not work because ck-editor plugin 'enterkey' ist not loaded on purpose by odoo!
            //config.enterMode = CKEDITOR.ENTER_P

            // Enable Force Paste As Plain Text
            config.forcePasteAsPlainText = true;

            // Add Custom font and font background colors
            config.colorButton_colors = 'CF5D4E,454545';

            // Add Plugin for print_field snippet
            // config.extraPlugins = 'sharedspace,customdialogs,tablebutton,oeref';
            // ATTENTION: the brangel addon protects <br> from beeing removed!
            config.extraPlugins = 'brangel,printfield,sharedspace,customdialogs,tablebutton,oeref';

            // Set custom toolbar
            // https://docs.ckeditor.com/ckeditor4/latest/guide/dev_toolbar.html
            config.toolbar = [{
                name: 'insert', items: [
                    "PrintField"
                ]
            }, {
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

            //console.log('config.allowedContent', config.allowedContent);
            //console.log('config.disallowedContent', config.disallowedContent);
            console.log('CKE config', config);

            // return the config
            return config;
        }

    });


})();
