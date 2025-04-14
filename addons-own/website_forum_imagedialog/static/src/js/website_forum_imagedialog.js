(function () {
    'use strict;'
    var website = openerp.website;
    var webEditor = website.editor;

    // Check if in ask/edit question
    if(!$('textarea.load_editor').length) {
//        console.log('not in forum');

        return $.Deferred().reject("DOM doesn't contain '.website_forum'");
    }
    $('textarea.load_editor').addClass('js_anchor')
    //--------------------------------------
    // Destroy and replace existing CKEditor
    //--------------------------------------
    CKEDITOR.instances['content'].on('loaded', function(ev) {
        if (CKEDITOR.instances['content']) {
            CKEDITOR.instances['content'].destroy(true);
        }
        CKEDITOR.replace('content', _forum_config());

        var editor = CKEDITOR.instances['content'];

        changeStyleInCKEDITOR(editor);

    });

    if (CKEDITOR.instances['content'].loaded) {
        if (CKEDITOR.instances['content']) {
            CKEDITOR.instances['content'].destroy(true);
        }
        CKEDITOR.replace('content', _forum_config());
    }

    var editor = CKEDITOR.instances['content'];
    changeStyleInCKEDITOR(editor);

    //--------------------------------------
    // Detect changes in editor and compute the Icon to get the correct color or delete the background
    //--------------------------------------
    function changeStyleInCKEDITOR (editor) {
        editor.on('change', function (ev) {
            var wfi_content = ev.editor.document.$.body.children;
            var iconHelper = ev.editor.document;

            computeIcon(wfi_content, iconHelper);
        });
    }

    // Compute the Icon and set the color and create new elements for background color
    function computeIcon(wfi_content, iconHelper) {
        var body = iconHelper.getBody();
        for (var i = 0; i < wfi_content.length; i++) {
            if (wfi_content[i].children.length) {
                var wfi_content_children = wfi_content[i].children;
                for (var j = 0; j < wfi_content_children.length; j++) {
                    if (wfi_content_children[j].children.length) {
                        var wfi_content_grandchildren = wfi_content_children[j].children;
                        for (var k = 0; k < wfi_content_grandchildren.length; k++) {
                            if (wfi_content_grandchildren[k].children.length) {
                                var wfi_content_grandchildren_deep = wfi_content_grandchildren[k].children;
                                for (var l = 0; l < wfi_content_grandchildren_deep.length; l++) {

                                    // Set icon to uneditable (no Text in span tag allowed)
                                    if (wfi_content_grandchildren_deep[l].className.match(/fa fa-(.*)/)) {
                                        setIconUneditable(wfi_content_grandchildren_deep[l]);
                                    }

                                    // Deletes Background Color from Icon and inserts new elements
                                    if (wfi_content_grandchildren_deep[l].style.backgroundColor) {
                                        computeIconBackgroundColor(wfi_content_grandchildren_deep[l], iconHelper);
                                    }
                                }
                            }
                            if (wfi_content_children[j].className.match(/fa fa-(.*)/)) {
                                if (wfi_content_grandchildren[k].style.color) {
                                    wfi_content_grandchildren[k].innerHTML = '<span class="' + wfi_content_children[j].className + '" contentEditable="false"></span> ';
                                    wfi_content_children[j].className = '';
                                    wfi_content_children[j].id = 'wfi_toRemove';
                                } else if (wfi_content_grandchildren[k].style.backgroundColor) {
                                    wfi_content_children[j].innerHTML = '<span class="' + wfi_content_children[j].className + '" contentEditable="false">';
                                    wfi_content_children[j].className = '';
                                    wfi_content_children[j].id = 'wfi_toRemove';
                                }
                            }

                            // Set icon to uneditable (no Text in span tag allowed)
                            if (wfi_content_grandchildren[k].className.match(/fa fa-(.*)/)) {
                                setIconUneditable(wfi_content_grandchildren[k]);
                            }

                            // Deletes Background Color from Icon and inserts new elements
                            if (wfi_content_grandchildren[k].style.backgroundColor) {
                                computeIconBackgroundColor(wfi_content_grandchildren[k], iconHelper);
                            }

                        }

                        // if icon exists before switch color or remove background color
                        if (wfi_content_children[j].id === 'wfi_toRemove') {
                            var element = iconHelper.getById('wfi_toRemove');
                            if (wfi_content_children[j].children[0].style.color) {
                                var tmp = wfi_content_children[j].innerHTML;
                                wfi_content_children[j].outerHTML = tmp;
                            } else if (wfi_content_children[j].children[0].style.backgroundColor) {
                                var tmpIcon = CKEDITOR.dom.element.createFromHtml(wfi_content_children[j].children[0].outerHTML);
                                tmpIcon.replace(element);
                            }
                        }

                    }

                    // if icon exists before color or background color
                    if (wfi_content[i].className.match(/fa fa-(.*)/)) {
                        if (wfi_content_children[j].style.color) {
                            wfi_content_children[j].innerHTML = '<span class="' + wfi_content[i].className + '" contentEditable="false"></span> ';
                            wfi_content[i].className = '';
                            wfi_content[i].id = 'wfi_toRemove_ParentIcon';
                        } else if (wfi_content_children[j].style.backgroundColor) {
                            wfi_content[i].innerHTML = '<span class="' + wfi_content[i].className + '" contentEditable="false">';
                            wfi_content[i].className = '';
                            wfi_content[i].id = 'wfi_toRemove_ParentIcon';
                        }
                    }

                    // Set icon to uneditable (no Text in span tag allowed)
                    if (wfi_content_children[j].className.match(/fa fa-(.*)/)) {
                        setIconUneditable(wfi_content_children[j]);
                    }

                    // Deletes Background Color from Icon and inserts new elements
                    if (wfi_content_children[j].style.backgroundColor) {
                        computeIconBackgroundColor(wfi_content_children[j], iconHelper);
                    }
                }

                // if icon exists before switch color or remove background color
                if (wfi_content[i].id === 'wfi_toRemove_ParentIcon') {
                    var element = iconHelper.getById('wfi_toRemove_ParentIcon');
                    if (wfi_content[i].children[0].style.color) {
                        var tmp = wfi_content[i].innerHTML;
                        wfi_content[i].outerHTML = tmp;
                    } else if (wfi_content[i].children[0].style.backgroundColor) {
                        var tmpIcon = CKEDITOR.dom.element.createFromHtml(wfi_content[i].children[0].outerHTML);
                        tmpIcon.replace(element);
                    }
                }
            }

            // Set icon to uneditable (no Text in span tag allowed)
            if (wfi_content[i].className.match(/fa fa-(.*)/)) {
                setIconUneditable(wfi_content[i]);
            }

            // Deletes Background Color from Icon and inserts new elements
            if (wfi_content[i].style.backgroundColor) {
                computeIconBackgroundColor(wfi_content[i], iconHelper);
            }
        }
    };

    // Set icon to uneditable (no Text in span tag allowed)
    function setIconUneditable (wfi_content) {
        if (wfi_content.attributes.length >= 2) {
            // Blocks the jump of the text after the icon
            if (wfi_content.attributes[1].nodeValue === false) {}
        } else {
            var tmp = '<span class="' + wfi_content.className + '" contentEditable="false"></span> ';
            wfi_content.outerHTML = tmp;
        }
    };

    // Deletes Background Color from Icon and inserts new elements
    function computeIconBackgroundColor (wfi_content, iconHelper) {
        var color = wfi_content.style.backgroundColor.match(/rgb(.*)/);
        if (wfi_content.childNodes.length === 1) {
            wfi_content.id = 'wfi_toReplace';
            var element = iconHelper.getById('wfi_toReplace');
            var tmpNodeIcon = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.childNodes[0].className + '" contentEditable="false"></span> ');
            tmpNodeIcon.replace(element);
        } else if (wfi_content.childNodes.length === 2) {
            wfi_content.id = 'wfi_toReplace';
            var element = iconHelper.getById('wfi_toReplace');
            var tmpNode1 = CKEDITOR.dom.element.createFromHtml('<span style="background-color:#' + fullColorHex(color[1]) + ';">' + wfi_content.childNodes[0].nodeValue + '</span>');
            var tmpNodeIcon = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.childNodes[1].className + '" contentEditable="false"></span> ');
            tmpNode1.replace(element);
            tmpNodeIcon.insertAfter(tmpNode1);
        } else if (wfi_content.childNodes.length === 3) {
            wfi_content.id = 'wfi_toReplace';
            var element = iconHelper.getById('wfi_toReplace');
            var tmpNode1 = CKEDITOR.dom.element.createFromHtml('<span style="background-color:#' + fullColorHex(color[1]) + ';">' + wfi_content.childNodes[0].nodeValue + '</span>');
            var tmpNodeIcon = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.childNodes[1].className + '" contentEditable="false"></span> ');
            var tmpNode2 = CKEDITOR.dom.element.createFromHtml('<span style="background-color:#' + fullColorHex(color[1]) + ';">' + wfi_content.childNodes[2].nodeValue + '</span>');
            tmpNode1.replace(element);
            tmpNodeIcon.insertAfter(tmpNode1);
            tmpNode2.insertAfter(tmpNodeIcon);
        }
    };

    function fullColorHex(rgb) {
        var color = rgb.replace(/[{()}]/g, '');
        color = color.split(', ')
        var red = rgbToHex(color[0]);
        var green = rgbToHex(color[1]);
        var blue = rgbToHex(color[2]);
        return red+green+blue;
    };

    function rgbToHex (rgb) {
        var hex = Number(rgb).toString(16);
        if (hex.length < 2) {
             hex = "0" + hex;
        }
        return hex;
    };

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
                if (element.$.className.indexOf(' fa-') != -1) {
                    element.removeAttribute('contentEditable');
                }

                if ((element.is('img') || element.$.className.indexOf(' fa-') != -1) && is_editable_node(element)) {
                    image_dialog(editor, element);
                    if (element.$.className.indexOf(' fa-') != -1) {
                        element.setAttribute('contentEditable', 'false');
                    }
                    return;
                }
                var parent = new CKEDITOR.dom.element(element.$.parentNode);
                if (parent.$.className.indexOf('media_iframe_video') != -1 && is_editable_node(parent)) {
                    image_dialog(editor, parent);
                    return;
                }

//                element = get_selected_link(editor) || evt.data.element;
//                if (!(element.is('a') && is_editable_node(element))) {
//                    return;
//                }
//
//                editor.getSelection().selectElement(element);
//                link_dialog(editor);
            }, null, null, 500);

//            //noinspection JSValidateTypes
//            editor.addCommand('link', {
//                exec: function (editor) {
//                    link_dialog(editor);
//                    return true;
//                },
//                canUndo: false,
//                editorFocus: true,
//                context: 'a',
//            });
            //noinspection JSValidateTypes
            editor.addCommand('cimage', {
                exec: function (editor) {
                    image_dialog(editor);
                    $('.btn.btn-primary.save').click(function() {
                        var wfi_content = editor.document.$.body.children;
                        var iconHelper = editor.document;
                        setTimeout(function() { computeIcon(wfi_content, iconHelper) }, 1000);

                    });
                    return true;
                },
                canUndo: false,
                editorFocus: true,
                context: 'img',
            });
//
//            editor.ui.addButton('Link', {
//                label: 'Link',
//                command: 'link',
//                toolbar: 'links,10',
//            });
            editor.ui.addButton('Image', {
                label: 'Image',
                command: 'cimage',
                toolbar: 'insert,10',
            });

            editor.addCommand( 'removeAnchor', new CKEDITOR.removeAnchorCommand() );
            editor.ui.addButton('removeAnchor', {
                label: 'Remove Anchor',
                command: 'removeAnchor',
                toolbar: 'insert,10',
                icon: '/website_forum_imagedialog/static/src/icons/anchor_remove.png'
            });
//
//            editor.addCommand('unlink', {
//                exec: function (editor) {
//                    editor.removeStyle(new CKEDITOR.style({
//                        element: 'a',
//                        type: CKEDITOR.STYLE_INLINE,
//                        alwaysRemoveElement: true,
//                    }));
//                },
//                canUndo: false,
//                editorFocus: true,
//            });
//            editor.ui.addButton('Unlink', {
//                label: 'Unlink',
//                command: 'unlink',
//                toolbar: 'links,11',
//            });
//
//            editor.setKeystroke(CKEDITOR.CTRL + 76 /*L*/, 'link');
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
            'floatpanel', 'panelbutton', 'link'
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
            allowedContent: true,/*{
                'p h1 li': {
                    styles: 'text-align, margin-left'
                },
                a: {
                    attributes: '!href'
                },
                'strong em u s sub sup br blockquote ol ul li': true,
                span: {
                    styles: 'color, background-color'
                },
            },*/
//			extraAllowedContent: '*(*)',
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
                    ]},{
                    name: 'links', items: [
                        "Anchor", "removeAnchor"
                    ]},{
                    name: 'basicstyles', items: [
                        "Underline", "Strike", "Subscript",
                        "Superscript", "TextColor", "BGColor", "RemoveFormat"
                    ]},{
                    name: 'justify', items: [
                        "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"
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



