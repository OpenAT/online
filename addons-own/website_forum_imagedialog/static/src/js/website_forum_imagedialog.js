(function () {
    'use strict;'
    var website = openerp.website;
    var webEditor = website.editor;

//    Check if in ask/edit question
    if(!$('textarea.load_editor').length) {
        console.log('not in forum');
        return $.Deferred().reject("DOM doesn't contain '.website_forum'");
    }

    website.EditorBar = openerp.Widget.extend({
        start: function() {
            var self = this;
            this.saving_mutex = new openerp.Mutex();

            this.$buttons = {
                edit: this.$el.parents().find('button[data-action=edit]'),
                save: this.$('button[data-action=save]'),
                cancel: this.$('button[data-action=cancel]'),
            };

            this.$('#website-top-edit').hide();
            this.$('#website-top-view').show();

            var $edit_button = this.$buttons.edit
                    .prop('disabled', website.no_editor);
            if (website.no_editor) {
                var help_text = $(document.documentElement).data('editable-no-editor');
                $edit_button.parent()
                    // help must be set on form above button because it does
                    // not appear on disabled button
                    .attr('title', help_text);
            }

            $('.dropdown-toggle').dropdown();

            this.$buttons.edit.click(function(ev) {
                self.edit();
            });
            this.rte = new website.RTE(this);
            this.rte.on('change', this, this.proxy('rte_changed'));
            this.rte.on('rte:ready', this, function () {
                self.setup_hover_buttons();
                self.trigger('rte:ready');
            });

            this.rte.appendTo(this.$('#website-top-edit .nav.js_editor_placeholder'));
            return this._super.apply(this, arguments);

        },

        setup_hover_buttons: function () {
            var editor = this.rte.wfi_editor;
            var $link_button = this.make_hover_button_link(function () {
                var sel = new CKEDITOR.dom.element(previous);
                editor.getSelection().selectElement(sel);
                if(sel.hasClass('fa')) {
                    new website.editor.MediaDialog(editor, previous)
                        .appendTo(document.body);
                } else if (previous.tagName.toUpperCase() === 'A') {
                    link_dialog(editor);
                }
                $link_button.hide();
                previous = null;
            });

            function is_icons_widget(element) {
                var w = editor.widgets.getByElement(element);
                return w && w.name === 'icons';
            }
        }
    });

    website.RTE.include({
        tagName: 'li',
        id: 'oe_rte_toolbar',
        className: 'oe_right oe_rte_toolbar',
        // editor.ui.items -> possible commands &al
        // editor.applyStyle(new CKEDITOR.style({element: "span",styles: {color: "#(color)"},overrides: [{element: "font",attributes: {color: null}}]}, {color: '#ff0000'}));

        init: function (EditorBar) {
            this.EditorBar = EditorBar;
            this._super.apply(this, arguments);
            this.start_forum_edition();
        },

        start_forum_edition: function () {
            var self = this;
            var def = $.Deferred();
            var forum = document.getElementById('wfi_editor');
            var old_editor = CKEDITOR.instances['content'];

            if (old_editor) {
                old_editor.destroy(true);
            }

            this.wfi_editor = CKEDITOR.replace('content', this._config());

        },

    });
})();
