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

            // Show E-Mail settings in edit mode by default
            $( "#email_template_settings" ).collapse('show');
            $( "#email_template_settings" ).addClass('in');

            return this._super.apply(this, arguments);
        }
    });

    // another try
    openerp.website.editor.RTELinkDialog = openerp.website.editor.RTELinkDialog.extend({

        bind_data: function () {
            // console.log('bind_data()');

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
            // console.log('make_link(): ' + classes);
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
            // console.log('make_link() after: ' + classes);
            return this._super(url, new_window, label, classes);
        },

    })

    // Add anchor to link dialog
    openerp.website.editor.RTELinkDialog = openerp.website.editor.RTELinkDialog.extend({
        /**
         * Allow the user to use only an anchor.
         */
        get_data: function (test) {
            var $anchor = this.$el.find("#anchor");

            if (test !== false && $anchor.val()) {
                var $url_source = this.$el
                                  .find(".active input.url-source:input"),
                    style = this.$el
                            .find("input[name='link-style-type']:checked")
                            .val(),
                    size = this.$el
                           .find("input[name='link-style-size']:checked")
                           .val(),
                    classes = (style && style.length ? "btn " : "") +
                              style + " " + size;

                return new $.Deferred().resolve(
                    $url_source.val() + "#" + $anchor.val(),
                    this.$el.find("input.window-new").prop("checked"),
                    this.$el.find("#link-text").val() || $url_source.val(),
                    classes);
            } else {
                return this._super(test);
            }
        },

        /**
         * Put data in its corresponding place in the link dialog.
         *
         * When user edits an existing link that contains an anchor, put it
         * in its field.
         */
        bind_data: function () {
            var url = this.element && (this.element.data("cke-saved-href")
                                   ||  this.element.getAttribute("href")),
                url_parts = url.split("#", 2),
                result = null;

            // Trick this._super()
            if (url_parts.length > 1) {
                this.element.setAttribute("href", url_parts[0]);
                this.element.data("cke-saved-href", url_parts[0])
                this.$el.find("#anchor").val(url_parts[1]);
            }

            result = this._super();

            // Back to expected status of this.element
            if (url_parts.length > 1) {
                this.element.setAttribute("href", url)
                this.element.data("cke-saved-href", url)
            }

            return result;
        },
    })

})();
