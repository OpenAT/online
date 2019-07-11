(function () {
    'use strict';

    CKEDITOR.plugins.add( 'printfield', {
        
        // ATTENTION: Must match the button name in lowercase
        icons: 'printfield',
        
        init: function( editor ) {
            
            editor.addCommand( 'insertPrintField', {
                exec: function( editor ) {
                    var printFieldSnippet = $('.oe_snippet_body.drop_in.drop_in_print_field');
                    if ( printFieldSnippet.length ) {
                        // clone the element to avoid editing the original
                        var printFieldSnippetClone = printFieldSnippet.clone();
                        // remove class .oe_snippet_body just like it would happen when drag and droppiung snippets
                        printFieldSnippetClone.removeClass("oe_snippet_body");
                        // insert the html at the cursor position
                        editor.insertHtml(printFieldSnippetClone[0].outerHTML);
                    }
                }
            });
            
            // ATTENTION: Button name must match the name in: "plugins.add( ... { icons: [buttonnamelowercase], ... "
            editor.ui.addButton( 'PrintField', {
                label: 'Insert Print Field',
                command: 'insertPrintField',
                toolbar: 'insert',
                icon: '/fso_website_email/static/src/icons/drop_in_print_field_toolbar.png'
            });
            
        }
    });

})();
