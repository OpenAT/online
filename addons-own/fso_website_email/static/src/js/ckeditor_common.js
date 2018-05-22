(function () {
    'use strict';

    openerp.website.EditorBar = openerp.website.EditorBar.extend({
        edit: function () {
            /**
             * website/static/src(js/website.editor.js@339
             *
             * This is called when the Edit button in the editor toolbar is clicked
             *
             * Allows to disable and enable ckeditor editing by classes for snipped dom elements.
             * Since classes will survive "saving" this will be reapplied on every edit start whereas
             * the "contenteditable" attribute would be removed on save!
             */
            $( "body .ckediting_disabled" ).attr( "contenteditable", "false" );
            $( "body .ckediting_enabled" ).attr( "contenteditable", "true" );

            $( "#email_template_settings" ).collapse('show');
            $( "#email_template_settings" ).addClass('in');

            return this._super.apply(this, arguments);
        }
    });

})();
