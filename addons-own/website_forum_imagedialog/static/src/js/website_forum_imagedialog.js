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
        var wfiStyleText = wfiClassName.match(/wfi_style_text_(.*)/);
        var wfiStyleIndent = wfiClassName.match(/wfi_style_indent_(.*)/);
        var wfiStyleColor = wfiClassName.match(/wfi_style_color_(.*)/);
        var wfiStyleBG = wfiClassName.match(/wfi_style_bgcolor_(.*)/);

        if (wfiStyleText) {
            $('.' + wfiClassName).attr('style', 'text-align:' + wfiStyleText[1] + ';');
        } else if (wfiStyleIndent) {
            $('.' + wfiClassName).attr('style', 'margin-left:' + wfiStyleIndent[1] + ';');
        } else if (wfiStyleColor) {
            $('.' + wfiClassName).attr('style', 'color:#' + wfiStyleColor[1] + ';');
        } else if (wfiStyleBG) {
            $('.' + wfiClassName).attr('style', 'background-color:#' + wfiStyleBG[1] + ';');
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
    var old_editor = CKEDITOR.instances['content'];

    if (old_editor) {
        old_editor.destroy(true);
    }

    CKEDITOR.replace('content', _forum_config());

    CKEDITOR.dtd.$removeEmpty.span = false;

    //--------------------------------------
    // Change of the EventNumber, because website_forum.js would change it to the wrong ones
    //--------------------------------------
    var editor = CKEDITOR.instances['content'];
    editor.on('instanceReady', CKEDITORLoadCompleteForum);

    //--------------------------------------
    // Apply Style in Editor when editing a Comment/Question
    //--------------------------------------
    editor.on('contentDom', function (ev) {
        var wfi_content = ev.editor.document.$.body.children;

        for (var i = 0; i < wfi_content.length; i++) {
            var wfiClassName = wfi_content[i].className;
            var wfiStyleText = wfiClassName.match(/wfi_style_text_(.*)/);
            var wfiStyleIndent = wfiClassName.match(/wfi_style_indent_(.*)/);

            if (wfiStyleText) {
                wfi_content[i].style.textAlign = wfiStyleText[1];
            } else if (wfiStyleIndent) {
                wfi_content[i].style.marginLeft = wfiStyleIndent[1];
            }

            if (wfi_content[i].children.length) {
                var wfi_content_children = wfi_content[i].children;
                for (var j = 0; j < wfi_content_children.length; j++) {
                    var wfiChildClassName = wfi_content_children[j].className;
                    var wfiStyleColor = wfiChildClassName.match(/wfi_style_color_(.*)/);
                    var wfiStyleBG = wfiChildClassName.match(/wfi_style_bgcolor_(.*)/);

                    if (wfiStyleColor) {
                        wfi_content_children[j].style.color = hexToRGB(wfiStyleColor[1]);
                    } else if (wfiStyleBG) {
                        wfi_content_children[j].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
                    }

                    if (wfi_content_children[j].children.length) {
                        if (wfi_content_children[j].children[0].className.match(/wfi_style_bgcolor_(.*)/)) {
                            wfiStyleBG = wfi_content_children[j].children[0].className.match(/wfi_style_bgcolor_(.*)/);
                            wfi_content_children[j].children[0].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
                        } else {

                            if (wfi_content_children[j].children[0].children.length) {
                                if (wfi_content_children[j].children[0].children[0].className.match(/wfi_style_bgcolor_(.*)/)) {
                                    wfiStyleBG = wfi_content_children[j].children[0].children[0].className.match(/wfi_style_bgcolor_(.*)/);
                                    wfi_content_children[j].children[0].children[0].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
                                } else {
                                    wfi_content_children[j]
                                }

                            } else if (wfi_content_children[j].children.length) {
                                var wfi_content_grandchildren = wfi_content_children[j].children;
                                for (var k = 0; k < wfi_content_grandchildren.length; k++) {
                                    if (wfi_content_grandchildren[k].className.match(/wfi_style_bgcolor_(.*)/)) {
                                        wfiStyleBG = wfi_content_grandchildren[k].className.match(/wfi_style_bgcolor_(.*)/)
                                        wfi_content_grandchildren[k].style.backgroundColor = hexToRGB(wfiStyleBG[1]);

                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    });

    function hexToRGB (hex) {
        r = parseInt(hex.substring(0,2), 16);
        g = parseInt(hex.substring(2,4), 16);
        b = parseInt(hex.substring(4,6), 16);

        result = 'rgb('+r+','+g+','+b+')';
        return result;
    }

    //--------------------------------------
    // To Bypass XSS adding Classnames to the new Style (for color and text positioning)
    // Also select content after color/background-color changed, because no correct behaviour (selection vanishes -->
    // next change: moves content from span with color or background-color deletes content) after changing to often
    //--------------------------------------
    editor.on('change', function (ev) {
        // Elements which need a classname
        var wfi_content = ev.editor.document.$.body.children;
        // Helpers to check if something changed in a deeper level
        var innerChanged = false;
        var innerGrandChanged = false;
        // For Selection of content after change
        var body = ev.editor.document.getBody();
        var selection = ev.editor.getSelection();
        var range = ev.editor.createRange();

        // Search elements and add classnames
        // 1.) check if children exist, if children exist go to second loop and check if there are 'grandchildren'
        // 2.) in children/grandchildren loop replace innerHtml and style for child/grandchild
        // 3.) add classname with color/background-color value
        // 4.) if no children exist, add only classname (for text alignment) or classname with color/background-color value
        for (var i = 0; i < wfi_content.length; i++) {

            if (wfi_content[i].children.length) {

                var wfi_content_children = wfi_content[i].children;
                for (var j = 0; j < wfi_content_children.length; j++) {

                    if (wfi_content_children[j].children.length) {
                        var wfi_content_grandchildren = wfi_content_children[j].children;
                        for (var k = 0; k < wfi_content_grandchildren.length; k++) {
                            if (wfi_content_grandchildren[k].style[0]) {
                                if (wfi_content_grandchildren[k].style.backgroundColor) {
                                    wfi_content_children[j].style.backgroundColor = wfi_content_grandchildren[k].style.backgroundColor;
                                    wfi_content_children[j].innerHTML = wfi_content_grandchildren[k].innerHTML;
                                    // select the current element
                                    range.selectNodeContents( body.getChild(j) );
                                    selection.selectRanges( [ range ] );
                                    innerGrandChanged = true;
                                }
                            }
                        }
                    }

                    var child_style = wfi_content_children[j].style;
                    if (child_style[0] && !innerGrandChanged) {
                        if (wfi_content_children[j].children.length){
                            if (wfi_content_children[j].children[0].className.indexOf('wfi_style_color_') > -1) {
                                wfi_content_children[j].innerHTML = wfi_content_children[j].children[0].innerHTML;
                                // select the current element
                                range.selectNodeContents( body.getChild(j) );
                                selection.selectRanges( [ range ] );
                                if (wfi_content_children[j].children[0]) {
                                    wfi_content_children[j].children[0].className = '';
                                }
                            }
                        }

                        if (wfi_content_children[j].style.color) {
                            var color = wfi_content_children[j].style.color.match(/rgb(.*)/);
                            wfi_content_children[j].className = 'wfi_style_color_' + fullColorHex(color[1]);
                            innerChanged = true;
                        }

                        if ((wfi_content_children[j].style.backgroundColor)) {
                            if (!wfi_content_children[j].parentElement.style.color) {
                                console.log(wfi_content_children[j].parentElement.style.color)
                                wfi_content[i].style.backgroundColor = wfi_content_children[j].style.backgroundColor;
                                wfi_content[i].innerHTML = wfi_content_children[j].innerHTML;
                                // select the current element
                                range.selectNodeContents( body.getChild(i) );
                                selection.selectRanges( [ range ] );
                            } else {
                                var color = wfi_content_children[j].style.backgroundColor.match(/rgb(.*)/);
                                wfi_content_children[j].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                                innerChanged = true;
                            }
                        }

                    }

                    if (innerGrandChanged) {
                        innerChanged = true;
                    }
                    innerGrandChanged = false;
                }
            }

            var parent_style = wfi_content[i].style;

            if (parent_style[0] && !innerChanged) {
                if (wfi_content[i].className.match(/wfi_style_text_(.*)/)) {
                    if (wfi_content[i].className === 'wfi_style_text_' + parent_style.textAlign) {
                        wfi_content[i].className = '';
                    } else if (wfi_content[i].className !== 'wfi_style_text_' + parent_style.textAlign) {
                        wfi_content[i].className = 'wfi_style_text_' + parent_style.textAlign;
                    }
                } else if (wfi_content[i].className.match(/wfi_style_indent_(.*)/)) {
                    wfi_content[i].className = '';
                    wfi_content[i].className = 'wfi_style_indent_' + parent_style.marginLeft;
                } else {
                    if (parent_style.textAlign) {
                        wfi_content[i].className = 'wfi_style_text_' + parent_style.textAlign;
                    } else if (parent_style.marginLeft) {
                        wfi_content[i].className = 'wfi_style_indent_' + parent_style.marginLeft;
                    }
                }

                if (parent_style.color) {
                    if (wfi_content[i].children.length) {
                        wfi_content[i].innerHTML = wfi_content[i].children[0].innerHTML;
                        // select the current element
                        range.selectNodeContents( body.getChild(i) );
                        selection.selectRanges( [ range ] );
                    }
                    var color = parent_style.color.match(/rgb(.*)/);
                    wfi_content[i].className = 'wfi_style_color_' + fullColorHex(color[1]);
                }

                if (parent_style.backgroundColor) {
                    var color = parent_style.backgroundColor.match(/rgb(.*)/);
                    wfi_content[i].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                }

            } else if (!parent_style[0]) {
                wfi_content[i].className = '';
            }

            innerChanged = false;
        }
    });

    function fullColorHex(rgb) {
        var color = rgb.replace(/[{()}]/g, '');
        color = color.split(', ')
        var red = rgbToHex(color[0]);
        var green = rgbToHex(color[1]);
        var blue = rgbToHex(color[2]);
        return red+green+blue;
    };

    var rgbToHex = function (rgb) {
        var hex = Number(rgb).toString(16);
        if (hex.length < 2) {
             hex = "0" + hex;
        }
        return hex;
    };

    function CKEDITORLoadCompleteForum(){
        $('.cke_button__link').attr('onclick','website_forum_IsKarmaValid(43,30)');
        $('.cke_button__image').attr('onclick','website_forum_IsKarmaValid(83,30)');
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
            extraPlugins: 'sharedspace,customdialogs_forum,tablebutton_forum,oeref_forum,fontawesome',
            contentsCss: '/web/static/lib/fontawesome/css/font-awesome.css',
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

