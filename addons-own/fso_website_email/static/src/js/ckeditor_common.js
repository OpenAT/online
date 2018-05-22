(function () {
    'use strict';

    openerp.website.EditorBar = openerp.website.EditorBar.extend({
        edit: function () {
            console.log('THIS WORKS');
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

            // Show E-Mail settings in edit mode by default
            $( "#email_template_settings" ).collapse('show');
            $( "#email_template_settings" ).addClass('in');

            return this._super.apply(this, arguments);
        }
    });

    // another try
    openerp.website.editor.RTELinkDialog = openerp.website.editor.RTELinkDialog.extend({
        bind_data: function () {
            // TODO: get classes 'link-donottrack' and 'link-withtoken' and update input fields accordingly
            var res = this._super();

            console.log('bind_data(): ' + this.element.getAttribute('class'));
            return res;
        },

        make_link: function (url, new_window, label, classes) {
            var res = this._super(url, new_window, label, classes);
            console.log('make_link(): ' + classes);

            var donottrack = this.$("input[name='link-donottrack']:checked").val();
            console.log('link-donottrack: ' + donottrack);

            var withtoken = this.$("input[name='link-withtoken']:checked").val();
            console.log('link-withtoken: ' + withtoken);

            // TODO: append classes if checkboxes are set
            classes += ' link-donottrack link-withtoken';
            console.log('classes after: ' + classes);

            return res;
        },

    })

})();
