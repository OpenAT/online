(function () {
    'use strict;'
    var website = openerp.website;
    var webEditor = website.editor;

    //--------------------------------------
    // Find the classnames of styled comments and apply the style to the elements
    //--------------------------------------
    var wfi_content = $('[class^="wfi_style_"]');
    for (var i = 0; i < wfi_content.length; i++) {
        var wfiClassName = wfi_content[i].className;
        var wfiStyleIndent = wfiClassName.match(/wfi_style_indent_(.*)/);

        if (wfiStyleIndent) {
            $('.' + wfiClassName).attr('style', 'margin-left:' + wfiStyleIndent[1] + ';');
        }
    }

    // Check if in ask/edit question
    if(!$('textarea.load_editor').length) {
//        console.log('not in forum');

        return $.Deferred().reject("DOM doesn't contain '.website_forum'");
    }

    //--------------------------------------
    // Destroy and replace existing CKEditor
    //--------------------------------------
    CKEDITOR.instances['content'].on('loaded', function(ev) {
        if (CKEDITOR.instances['content']) {
            CKEDITOR.instances['content'].destroy(true);
        }
        CKEDITOR.replace('content', _forum_config());

        var editor = CKEDITOR.instances['content'];

        loadStyleInCKEDITOR(editor);
        changeStyleInCKEDITOR(editor);

    });

    if (CKEDITOR.instances['content'].loaded) {
        if (CKEDITOR.instances['content']) {
            CKEDITOR.instances['content'].destroy(true);
        }
        CKEDITOR.replace('content', _forum_config());
    }

//    CKEDITOR.dtd.$removeEmpty.span = false;

    var editor = CKEDITOR.instances['content'];
    loadStyleInCKEDITOR(editor);
    changeStyleInCKEDITOR(editor);

    //--------------------------------------
    // Apply Style in Editor when editing a Comment/Question
    //--------------------------------------
    function loadStyleInCKEDITOR (editor) {
        editor.on('contentDom', function (ev) {
            var wfi_content = ev.editor.document.$.body.children;

            for (var i = 0; i < wfi_content.length; i++) {
                var wfiClassName = wfi_content[i].className;
                var wfiStyleIndent = wfiClassName.match(/wfi_style_indent_(.*)/);

                if (wfiStyleIndent) {
                    wfi_content[i].style.marginLeft = wfiStyleIndent[1];
                }
            }
        });
    }

    //--------------------------------------
    // To Bypass XSS adding Classnames to the new Style (text positioning)
    //--------------------------------------
    function changeStyleInCKEDITOR (editor) {
        editor.on('change', function (ev) {
            // Elements which need a classname
            var wfi_content = ev.editor.document.$.body.children;

            for (var i = 0; i < wfi_content.length; i++) {

                var parent_style = wfi_content[i].style;

                if (wfi_content[i].className.match(/wfi_style_indent_(.*)/)) {
                    wfi_content[i].className = '';
                    wfi_content[i].className = 'wfi_style_indent_' + parent_style.marginLeft;
                }
                if (parent_style.marginLeft) {
                    wfi_content[i].className = 'wfi_style_indent_' + parent_style.marginLeft;
                }
            }
        });
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
        return new webEditor.RTELinkDialog(editor).appendTo(document.body);
    }
    function image_dialog(editor, image) {
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

            editor.addCommand('unlink', {
                exec: function (editor) {
                    editor.removeStyle(new CKEDITOR.style({
                        element: 'a',
                        type: CKEDITOR.STYLE_INLINE,
                        alwaysRemoveElement: true,
                    }));
                },
                canUndo: false,
                editorFocus: true,
            });
            editor.ui.addButton('Unlink', {
                label: 'Unlink',
                command: 'unlink',
                toolbar: 'links,11',
            });

            editor.setKeystroke(CKEDITOR.CTRL + 76 /*L*/, 'link');
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
                        allowedContent: true
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
                        allowedContent: true
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

    CKEDITOR.plugins.addExternal( 'fontawesome', '/website_forum_imagedialog/static/src/plugin/fontawesome/plugin.js' );

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
            'table', 'templates', 'toolbar', 'undo', 'wysiwygarea',
            'floatpanel', 'panelbutton'
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
            extraAllowedContent: 'span style',
            // Don't insert paragraphs around content in e.g. <li>
            autoParagraph: false,
            // Don't automatically add &nbsp; or <br> in empty block-level
            // elements when edition starts
            fillEmptyBlocks: false,
            filebrowserImageUploadUrl: "/website/attach",
            // Support for sharedSpaces in 4.x
            extraPlugins: 'sharedspace,customdialogs_forum,oeref_forum,fontawesome',
            contentsCss: '/web/static/lib/fontawesome/css/font-awesome.css',
            // Place toolbar in controlled location
            sharedSpaces: { top: 'oe_rte_toolbar' },
            toolbar: [{
                    name: 'basicstyles', items: [
                    "Bold", "Italic"
                ]},{
                name: 'paragraph', items: [
                    "NumberedList", "BulletedList", "Blockquote"
                ]},{
                name: 'span', items: [
                    "Indent", "Outdent", "Link", "Unlink", "Image"
                ]}
            ],
        };
    }
})();

