(function () {
    'use strict';

    openerp.website.EditorBar.include({
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

            // Show E-Mail settings in edit mode by default
            $( "#email_template_settings" ).collapse('show');
            $( "#email_template_settings" ).addClass('in');

            // Bind event to get_text_from_html button
            // $("#get_text_from_html").on("click", function () {
            //     console.log('so ein dreck');
            //     $("#fso_email_text").html($('#email_body_html').text());
            // });

            return this._super.apply(this, arguments);
        }
    });

    // another try
    // console.log('RTELinkDialog BEFORE:', openerp.website.editor.RTELinkDialog);
    openerp.website.editor.RTELinkDialog.include({

        bind_data: function () {
            console.log('bind_data()');

            var classes = null;
            classes = this.element && this.element.getAttribute("class") || '';
            // console.log('bind_data() this.element.class: ' + classes);

            // search for class in classes
            var donottrack = classes.indexOf('link-donottrack') !== -1;
            var withtoken  = classes.indexOf('link-withtoken') !== -1;

            // set input fields in link dialog
            this.$("input[class='link-donottrack']").prop('checked', donottrack);
            this.$("input[class='link-withtoken']").prop('checked', withtoken);

            var result = null;
            result = this._super();

            return result;
        },

        make_link: function (url, new_window, label, classes) {
            console.log('make_link(): ' + classes);
            classes = classes.replace(/undefined/g, '') || '';
            classes = classes.replace(/\s{2,}/g, ' ').trim();

            // do not track
            if (this.$("input[class='link-donottrack']").prop("checked")) {
                classes += ' link-donottrack';
            }
            else {
                classes = classes.replace(/link-donottrack/g, '')
            }

            // with token
            if (this.$("input[class='link-withtoken']").prop("checked")) {
                classes += ' link-withtoken';
            }
            else {
                classes = classes.replace(/link-withtoken/g, '')
            }

            classes = classes.replace(/\s{2,}/g, ' ').trim();

            if (!(classes && classes.length)) {
                // Base class is coded to ignore empty classes.
                // To trick the base class, an array with a null
                // element is sent instead of a string.
                classes = [ null ];
            }
            // console.log('make_link() after: ' + classes);
            return this._super(url, new_window, label, classes);
        },

    });
    // console.log('RTELinkDialog AFTER:', openerp.website.editor.RTELinkDialog);


})();
