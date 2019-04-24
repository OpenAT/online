(function () {
    'use strict;'
    var website = openerp.website;
    var webEditor = website.editor;

    // Check if in ask/edit question
    if(!$('textarea.load_editor').length) {
        console.log('not in forum');
        return $.Deferred().reject("DOM doesn't contain '.website_forum'");
    }

    //--------------------------------------
    // Destroy and replace existing CKEditor
    //--------------------------------------
    var old_editor = CKEDITOR.instances['content'];

    if (old_editor) {
        old_editor.destroy(true);
    }

    CKEDITOR.replace('content', _forum_config());

    //--------------------------------------
    // Change of the EventNumber, because website_forum.js would change it to the wrong ones
    //--------------------------------------
    var editor = CKEDITOR.instances['content'];
    editor.on('instanceReady', CKEDITORLoadCompleteForum);

    function CKEDITORLoadCompleteForum(){
        $('.cke_button__link').attr('onclick','website_forum_IsKarmaValid(41,30)');
        $('.cke_button__image').attr('onclick','website_forum_IsKarmaValid(81,30)');
        $('.cke_button__link').attr('class', 'cke_button__link_1 cke_button cke_button_off');
        $('.cke_button__image').attr('class', 'cke_button__image_1 cke_button cke_button_off');
    }

    //----------------------------------------
    // Copy of the Odoo Toolbar in the Edit Mode
    //----------------------------------------
    function is_editing_host(element) {
        return element.getAttribute('contentEditable') === 'true';
    }

    function is_editable_node(element) {
        return !(element.data('oe-model') === 'ir.ui.view'
              || element.data('cke-realelement')
              || (is_editing_host(element) && element.getAttribute('attributeEditable') !== 'true')
              || element.isReadOnly());
    }

    function link_dialog(editor) {
        console.log('link')
        console.log(editor)
        return new webEditor.RTELinkDialog(editor).appendTo(document.body);
    }
    function image_dialog(editor, image) {
        console.log('image')
        console.log(editor)
        return new webEditor.MediaDialog(editor, image).appendTo(document.body);
    }

    function get_selected_link(editor) {
        var sel = editor.getSelection(),
            el = sel.getSelectedElement();
        if (el && el.is('a')) { return el; }

        var range = sel.getRanges(true)[0];
        if (!range) { return null; }

        range.shrink(CKEDITOR.SHRINK_TEXT);
        var commonAncestor = range.getCommonAncestor();
        var viewRoot = editor.elementPath(commonAncestor).contains(function (element) {
            return element.data('oe-model') === 'ir.ui.view';
        });
        if (!viewRoot) { return null; }
        // if viewRoot is the first link, don't edit it.
        return new CKEDITOR.dom.elementPath(commonAncestor, viewRoot)
                .contains('a', true);
    }

    CKEDITOR.plugins.add('customdialogs_forum', {
        // requires: 'link,image',
        init: function (editor) {
            console.log(editor)
            editor.on('doubleclick', function (evt) {
                var element = evt.data.element;
                if ((element.is('img') || element.$.className.indexOf(' fa-') != -1) && is_editable_node(element)) {
                    image_dialog(editor, element);
                    return;
                }
                var parent = new CKEDITOR.dom.element(element.$.parentNode);
                if (parent.$.className.indexOf('media_iframe_video') != -1 && is_editable_node(parent)) {
                    image_dialog(editor, parent);
                    return;
                }

                element = get_selected_link(editor) || evt.data.element;
                if (!(element.is('a') && is_editable_node(element))) {
                    return;
                }

                editor.getSelection().selectElement(element);
                link_dialog(editor);
            }, null, null, 500);

            //noinspection JSValidateTypes
            editor.addCommand('link', {
                exec: function (editor) {
                    link_dialog(editor);
                    return true;
                },
                canUndo: false,
                editorFocus: true,
                context: 'a',
            });
            //noinspection JSValidateTypes
            editor.addCommand('cimage', {
                exec: function (editor) {
                    image_dialog(editor);
                    return true;
                },
                canUndo: false,
                editorFocus: true,
                context: 'img',
            });

            editor.ui.addButton('Link', {
                label: 'Link',
                command: 'link',
                toolbar: 'links,10',
            });
            editor.ui.addButton('Image', {
                label: 'Image',
                command: 'cimage',
                toolbar: 'insert,10',
            });

            editor.setKeystroke(CKEDITOR.CTRL + 76 /*L*/, 'link');
        }
    });

    CKEDITOR.plugins.add( 'tablebutton_forum', {
        requires: 'panelbutton,floatpanel',
        init: function( editor ) {
            var label = "Table";
            editor.ui.add('TableButton', CKEDITOR.UI_PANELBUTTON, {
                label: label,
                title: label,
                // use existing 'table' icon
                icon: 'table',
                modes: { wysiwyg: true },
                editorFocus: true,
                // panel opens in iframe, @css is CSS file <link>-ed within
                // frame document, @attributes are set on iframe itself.
                panel: {
                    css: '/website/static/src/css/editor.css',
                    attributes: { 'role': 'listbox', 'aria-label': label, },
                },

                onBlock: function (panel, block) {
                    block.autoSize = true;
                    block.element.setHtml(openerp.qweb.render('website.editor.table.panel', {
                        rows: 5,
                        cols: 5,
                    }));

                    var $table = $(block.element.$).on('mouseenter', 'td', function (e) {
                        var $e = $(e.target);
                        var y = $e.index() + 1;
                        var x = $e.closest('tr').index() + 1;

                        $table
                            .find('td').removeClass('selected').end()
                            .find('tr:lt(' + String(x) + ')')
                            .children().filter(function () { return $(this).index() < y; })
                            .addClass('selected');
                    }).on('click', 'td', function (e) {
                        var $e = $(e.target);

                        //noinspection JSPotentiallyInvalidConstructorUsage
                        var table = new CKEDITOR.dom.element(
                            $(openerp.qweb.render('website.editor.table', {
                                rows: $e.closest('tr').index() + 1,
                                cols: $e.index() + 1,
                            }))[0]);

                        editor.insertElement(table);
                        setTimeout(function () {
                            //noinspection JSPotentiallyInvalidConstructorUsage
                            var firstCell = new CKEDITOR.dom.element(table.$.rows[0].cells[0]);
                            var range = editor.createRange();
                            range.moveToPosition(firstCell, CKEDITOR.POSITION_AFTER_START);
                            range.select();
                        }, 0);
                    });

                    block.element.getDocument().getBody().setStyle('overflow', 'hidden');
                    CKEDITOR.ui.fire('ready', this);
                },
            });
        }
    });

    CKEDITOR.plugins.add('oeref_forum', {
        requires: 'widget',

        init: function (editor) {
            var specials = {
                // Can't find the correct ACL rule to only allow img tags
                image: { content: '*' },
                html: { text: '*' },
                monetary: {
                    text: {
                        selector: 'span.oe_currency_value',
                        allowedContent: { }
                    }
                }
            };
            _(specials).each(function (editable, type) {
                editor.widgets.add(type, {
                    draggable: false,
                    editables: editable,
                    upcast: function (el) {
                        return  el.attributes['data-oe-type'] === type;

                    }
                });
            });
            editor.widgets.add('oeref', {
                draggable: false,
                editables: {
                    text: {
                        selector: '*',
                        allowedContent: { }
                    },
                },
                upcast: function (el) {
                    var type = el.attributes['data-oe-type'];
                    if (!type || (type in specials)) {
                        return false;
                    }
                    if (el.attributes['data-oe-original']) {
                        while (el.children.length) {
                            el.children[0].remove();
                        }
                        el.add(new CKEDITOR.htmlParser.text(
                            el.attributes['data-oe-original']
                        ));
                    }
                    return true;
                }
            });

            editor.widgets.add('icons', {
                draggable: false,

                init: function () {
                    this.on('edit', function () {
                        new webEditor.MediaDialog(editor, this.element)
                            .appendTo(document.body);
                    });
                },
                upcast: function (el) {
                    return el.hasClass('fa')
                        // ignore ir.ui.view (other data-oe-model should
                        // already have been matched by oeref and
                        // monetary?
                        && !el.attributes['data-oe-model'];
                }
            });
        }
    });

    function _forum_config() {
        // base plugins minus
        // - magicline (captures mousein/mouseout -> breaks draggable)
        // - contextmenu & tabletools (disable contextual menu)
        // - bunch of unused plugins
        var plugins = [
            'a11yhelp', 'basicstyles', 'blockquote',
            'clipboard', 'colorbutton', 'colordialog', 'dialogadvtab',
            'elementspath', /*'enterkey',*/ 'entities', 'filebrowser',
            'find', 'floatingspace','format', 'htmlwriter', 'iframe',
            'indentblock', 'indentlist', 'justify',
            'list', 'pastefromword', 'pastetext', 'preview',
            'removeformat', 'resize', 'save', 'selectall', 'stylescombo',
            'table', 'templates', 'toolbar', 'undo', 'wysiwygarea'
        ];
        return {
            // FIXME
            language: 'en',
            // Disable auto-generated titles
            // FIXME: accessibility, need to generate user-sensible title, used for @title and @aria-label
            title: false,
            plugins: plugins.join(','),
            uiColor: '',
            // FIXME: currently breaks RTE?
            // Ensure no config file is loaded
            customConfig: '',
            // Disable ACF
            allowedContent: true,
            // Don't insert paragraphs around content in e.g. <li>
            autoParagraph: false,
            // Don't automatically add &nbsp; or <br> in empty block-level
            // elements when edition starts
            fillEmptyBlocks: false,
            filebrowserImageUploadUrl: "/website/attach",
            // Support for sharedSpaces in 4.x
            extraPlugins: 'sharedspace,customdialogs_forum,tablebutton_forum,oeref_forum',
            // Place toolbar in controlled location
            sharedSpaces: { top: 'oe_rte_toolbar' },
            toolbar: [{
                    name: 'basicstyles', items: [
                    "Bold", "Italic", "Underline", "Strike", "Subscript",
                    "Superscript", "TextColor", "BGColor", "RemoveFormat"
                ]},{
                name: 'span', items: [
                    "Link", "Blockquote", "BulletedList",
                    "NumberedList", "Indent", "Outdent"
                ]},{
                name: 'justify', items: [
                    "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"
                ]},{
                name: 'special', items: [
                    "Image", "TableButton"
                ]},{
                name: 'styles', items: [
                    "Styles"
                ]}
            ],
            // styles dropdown in toolbar
            stylesSet: [
                {name: "Normal", element: 'p'},
                {name: "Heading 1", element: 'h1'},
                {name: "Heading 2", element: 'h2'},
                {name: "Heading 3", element: 'h3'},
                {name: "Heading 4", element: 'h4'},
                {name: "Heading 5", element: 'h5'},
                {name: "Heading 6", element: 'h6'},
                {name: "Formatted", element: 'pre'},
                {name: "Address", element: 'address'}
            ],
        };
    }
})();

