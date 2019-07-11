(function () {
    'use strict';

    CKEDITOR.plugins.add( 'print_field', {
        icons: 'drop_in_print_field',
        init: function( editor ) {
            editor.addCommand( 'printField', {
                exec: function( editor ) {
                    var printField = $('.ckediting_disabled.drop_in.drop_in_print_field.pf_vorname');
                    editor.insertHtml(printField[0].outerHTML);
                }
            });
            editor.ui.addButton( 'PrintField', {
                label: 'Print Field',
                command: 'printField',
                toolbar: 'insert'
            });

            //When a ckeditor with this plugin in it is created, find the button
            //in the current instance and add the icon
            CKEDITOR.on("instanceReady", function(event) {
                var button = $('.cke_button_icon.cke_button__printfield_icon')

                if(typeof button != 'undefined') {
                    button[0].innerHTML = '<img id="cke_print_field_img" src="/fso_website_email/static/src/icons/drop_in_print_field_toolbar.png"/>';
                    // Setting width to display button correctly
                    $('.cke_button.cke_button__printfield.cke_button_off').css({'width': '45px'});

                }
            });
        }
    });

})();
