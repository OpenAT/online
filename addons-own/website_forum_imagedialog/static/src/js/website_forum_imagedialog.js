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
//        var wfiStyleBG = wfiClassName.match(/wfi_style_bgcolor_(.*)/);

        if (wfiStyleText) {
            $('.' + wfiClassName).attr('style', 'text-align:' + wfiStyleText[1] + ';');
        } else if (wfiStyleIndent) {
            $('.' + wfiClassName).attr('style', 'margin-left:' + wfiStyleIndent[1] + ';');
        } else if (wfiStyleColor) {
            $('.' + wfiClassName).attr('style', 'color:#' + wfiStyleColor[1] + ';');
        } /*else if (wfiStyleBG) {
            $('.' + wfiClassName).attr('style', 'background-color:#' + wfiStyleBG[1] + ';');
        }*/
    }

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
//    CKEDITOR.dtd.$removeEmpty.div = false;
//    CKEDITOR.dtd.$removeEmpty.br = false;

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
//                        var wfiStyleBG = wfiChildClassName.match(/wfi_style_bgcolor_(.*)/);

                        if (wfiStyleColor) {
                            wfi_content_children[j].style.color = hexToRGB(wfiStyleColor[1]);
                        } /*else if (wfiStyleBG) {
                            wfi_content_children[j].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
                        }*/

                        if (wfi_content_children[j].children.length) {
                            if (wfi_content_children[j].children[0].className.match(/wfi_style_color_(.*)/)) {
                                wfiStyleColor = wfi_content_children[j].children[0].className.match(/wfi_style_color_(.*)/);
                                wfi_content_children[j].children[0].style.color = hexToRGB(wfiStyleColor[1]);
                            }

//                            if (wfi_content_children[j].children[0].className.match(/wfi_style_bgcolor_(.*)/)) {
//                                wfiStyleBG = wfi_content_children[j].children[0].className.match(/wfi_style_bgcolor_(.*)/);
//                                wfi_content_children[j].children[0].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
//                            } else {
//
//                                if (wfi_content_children[j].children[0].children.length) {
//                                    if (wfi_content_children[j].children[0].children[0].className.match(/wfi_style_bgcolor_(.*)/)) {
//                                        wfiStyleBG = wfi_content_children[j].children[0].children[0].className.match(/wfi_style_bgcolor_(.*)/);
//                                        wfi_content_children[j].children[0].children[0].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
//                                    } else {
//                                        wfi_content_children[j]
//                                    }
//
//                                } else if (wfi_content_children[j].children.length) {
//                                    var wfi_content_grandchildren = wfi_content_children[j].children;
//                                    for (var k = 0; k < wfi_content_grandchildren.length; k++) {
//                                        if (wfi_content_grandchildren[k].className.match(/wfi_style_bgcolor_(.*)/)) {
//                                            wfiStyleBG = wfi_content_grandchildren[k].className.match(/wfi_style_bgcolor_(.*)/)
//                                            wfi_content_grandchildren[k].style.backgroundColor = hexToRGB(wfiStyleBG[1]);
//
//                                        }
//                                    }
//                                }
//                            }
                        }
                    }
                }
            }
        });
    }

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
    function changeStyleInCKEDITOR (editor) {
        if ($('.btn.btn-primary.save').length) {
            console.log('jquery click')
            $('.btn.btn-primary.save').click(function() {
                editor.fire('change');
            });
        }

        editor.on('change', function (ev) {
            // Elements which need a classname
            var wfi_content = ev.editor.document.$.body.children;
            // Helpers to check if something changed in a deeper level
            var innerChanged = false;
            var innerGrandChanged = false;
            var changeOccured = false;
            var iconHelper = ev.editor.document;
            // For Selection of content after change
            var body = ev.editor.document.getBody();
            var selection = ev.editor.getSelection();
            var range = ev.editor.createRange();

            // Search elements and add classnames
            // 1.) check if children exist, if children exist go to second loop and check if there are 'grandchildren'
            // 2.) in children/grandchildren loop replace innerHtml and style for child/grandchild
            // 3.) add classname with color/background-color value
            // 4.) if no children exist, add only classname (for text alignment) or classname with color/background-color value
            computeIcon(wfi_content, iconHelper);
            for (var i = 0; i < wfi_content.length; i++) {
//                console.log(wfi_content)
                if (wfi_content[i].children.length) {
                    var wfi_content_children = wfi_content[i].children;
                    for (var j = 0; j < wfi_content_children.length; j++) {

                        if (wfi_content_children[j].children.length) {
                            var wfi_content_grandchildren = wfi_content_children[j].children;
                            for (var k = 0; k < wfi_content_grandchildren.length; k++) {
                                if (wfi_content_grandchildren[k].children.length) {
                                    var wfi_content_grandchildren_deep = wfi_content_grandchildren[k].children;
                                    for (var l = 0; l < wfi_content_grandchildren_deep.length; l++) {
                                        console.log(wfi_content_grandchildren_deep[l])
                                        if (wfi_content_grandchildren_deep[l].children.length) {
                                                console.log('grand deep deep')
                                                wfi_content_grandchildren[k].children[0].style.backgroundColor = wfi_content_grandchildren[k].children[0].children[0].style.backgroundColor;
                                                wfi_content_grandchildren[k].children[0].innerText = wfi_content_grandchildren[k].children[0].children[0].innerHTML;
                                                changeOccured = true;
                                        }

                                        if (wfi_content_grandchildren_deep[l].style.backgroundColor && !wfi_content_grandchildren[k].style.color && !wfi_content_grandchildren_deep[l].className.match(/wfi_style_bgcolor_(.*)/)) {
                                            console.log('grand deep replace bg')
                                            wfi_content_grandchildren[k].style.backgroundColor = wfi_content_grandchildren[k].children[0].style.backgroundColor;
                                            wfi_content_grandchildren[k].innerText = wfi_content_grandchildren[k].children[0].innerHTML;
                                            changeOccured = true;
                                        } else if (wfi_content_grandchildren_deep[l].style.backgroundColor && !wfi_content_grandchildren_deep[l].className.match(/wfi_style_bgcolor_(.*)/)) {
                                            console.log('grand deep set bg')
                                            var color = wfi_content_grandchildren_deep[l].style.backgroundColor.match(/rgb(.*)/);
                                            wfi_content_grandchildren_deep[l].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                                        }
                                    }
                                }

                                if (wfi_content_grandchildren[k].style[0]) {
                                    console.log('grandchildren')
                                        console.log(wfi_content_grandchildren[k])

                                    if (wfi_content_grandchildren[k].className.match(/fa fa-(.*)/)) {
                                        console.log('grandchild icon')
                                        console.log(wfi_content_grandchildren[k])
                                        innerGrandChanged = true;
                                    }

                                    if (wfi_content_grandchildren[k].style.backgroundColor && !wfi_content_grandchildren[k].className.match(/wfi_style_bgcolor_(.*)/)) {
                                        console.log('grand bg color check')
                                        var color = wfi_content_grandchildren[k].style.backgroundColor.match(/rgb(.*)/);
                                        wfi_content_grandchildren[k].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                                        innerGrandChanged = true;
                                    } else if (wfi_content_grandchildren[k].style.color && !wfi_content_grandchildren[k].className.match(/wfi_style_color_(.*)/)) {
                                        console.log('grand child color')
                                        if (wfi_content_grandchildren[k].children.length) {
                                            if (wfi_content_grandchildren[k].children[0].className.indexOf('wfi_style_color_') > -1) {
                                                console.log('grandchild deep color')

                                                wfi_content_grandchildren[k].innerHTML = wfi_content_grandchildren[k].children[0].innerHTML;

                                                if (wfi_content_grandchildren[k].children[0]) {
                                                    wfi_content_grandchildren[k].children[0].className = '';
                                                }
                                                innerGrandChanged = true;
                                            }
                                        }

                                        if (!innerGrandChanged) {
                                            console.log('first color grandchild')
                                            var color = wfi_content_grandchildren[k].style.color.match(/rgb(.*)/);
                                            wfi_content_grandchildren[k].className = 'wfi_style_color_' + fullColorHex(color[1]);
                                            innerGrandChanged = true;
                                        }
                                    }

                                    if (changeOccured) {
                                        var color;

                                        if (wfi_content_grandchildren[k].style.color) {
                                            color = wfi_content_grandchildren[k].style.color.match(/rgb(.*)/);
                                            wfi_content_grandchildren[k].className = 'wfi_style_color_' + fullColorHex(color[1]);
                                        } else if (wfi_content_grandchildren[k].style.backgroundColor) {
                                            color = wfi_content_grandchildren[k].style.backgroundColor.match(/rgb(.*)/);
                                            wfi_content_grandchildren[k].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                                        }

                                        // select the current element
                                        for (var n = 0; n < body.getChildCount(); n++) {
                                            if (body.getChild(n).$.childNodes.length > 0)  {
                                                var childNodes = body.getChild(n).$.childNodes;
                                                for (var m = 0; m < childNodes.length; m++) {
                                                    if (wfi_content_children[j].className === childNodes[m].className) {
                                                        range.selectNodeContents( body.getChild(n).getChild(m) );
                                                        selection.selectRanges( [ range ] );
                                                    }
                                                }
                                            }
                                        }
                                        innerGrandChanged = true;
                                        changeOccured = false;
                                    }
                                }
                            }
                        }

                        var child_style = wfi_content_children[j].style;
                        if (child_style[0] && !innerGrandChanged) {
                            console.log('child style')
//                            if (wfi_content_children[j].children.length && !wfi_content_children[j].className.match(/wfi_style_color_(.*)/)) {
//                                console.log('child style test')
////                                if (wfi_content_children[j].children[0].className.indexOf('wfi_style_color_') > -1) {
////                                    console.log('color grand')
////                                    wfi_content_children[j].innerHTML = wfi_content_children[j].children[0].innerHTML;
//////                                    changeOccured = true;
////                                }
//                            }

                            if (wfi_content_children[j].style.color && !wfi_content_children[j].className.match(/wfi_style_color_(.*)/)) {
                                console.log('child color')
                                if (wfi_content_children[j].children.length && !wfi_content_children[j].children[0].className.match(/fa fa-(.*)/)) {
                                    console.log('reset color')
                                    var color = child_style.color.match(/rgb(.*)/);
                                    wfi_content_children[j].className = 'wfi_style_color_' + fullColorHex(color[1]);
                                    wfi_content_children[j].innerHTML = wfi_content_children[j].children[0].innerHTML;

                                    changeOccured = true;
                                } else if (!wfi_content_children[j].className) {
                                    console.log('set color')
                                    var color = wfi_content_children[j].style.color.match(/rgb(.*)/);
                                    wfi_content_children[j].className = 'wfi_style_color_' + fullColorHex(color[1]);
                                    innerChanged = true;
                                }
                            }

                            if (wfi_content_children[j].style.backgroundColor && !wfi_content[i].className.match(/wfi_style_bgcolor_(.*)/)) {
                                console.log('child bg')
                                if (wfi_content[i].className.match(/wfi_style_bgcolor_(.*)/)) {
                                    console.log('reset bg')
                                    wfi_content[i].style.backgroundColor = wfi_content_children[j].style.backgroundColor;
                                    wfi_content[i].innerHTML = wfi_content_children[j].innerHTML;

                                } else if (!wfi_content_children[j].className) {
                                    console.log('set bg')
                                    var color = wfi_content_children[j].style.backgroundColor.match(/rgb(.*)/);
                                    wfi_content_children[j].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                                    innerChanged = true;
                                }
                            }

                            if (changeOccured) {
                                console.log('change occured')
                                // select the current element
                                var color;
                                if (wfi_content_children[j].style.color) {
                                    color = wfi_content_children[j].style.color.match(/rgb(.*)/);
                                    wfi_content_children[j].className = 'wfi_style_color_' + fullColorHex(color[1]);
                                } else if (wfi_content_children[j].style.backgroundColor) {
                                    color  = wfi_content_children[j].style.backgroundColor.match(/rgb(.*)/);
                                    wfi_content_children[j].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
                                }

                                for (var n = 0; n < body.getChildCount(); n++) {
                                    if (body.getChild(n).$.childNodes.length > 0)  {
                                        var childNodes = body.getChild(n).$.childNodes;
                                        for (var m = 0; m < childNodes.length; m++) {
                                            if (wfi_content_children[j].className === childNodes[m].className) {
                                                range.selectNodeContents( body.getChild(n).getChild(m) );
                                                selection.selectRanges( [ range ] );
                                            }
                                        }
                                    }
                                }
                                if (wfi_content_children[j].children[0]) {
                                    wfi_content_children[j].children[0].className = '';
                                }
                                innerChanged = true;
                                changeOccured = false;
                            }
                        }

                        if (innerGrandChanged) {
                            innerChanged = true;
                        }
                        innerGrandChanged = false;
                    }
                }

                var parent_style = wfi_content[i].style;
                if (parent_style[0] && !wfi_content[i].className.match(/wfi_style_(.*)/)) {
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
                        console.log('parent color')
                        if (wfi_content[i].children.length && !wfi_content[i].children[0].className.match(/fa fa-(.*)/)) {
                            console.log('parent child color')
                            var color = parent_style.color.match(/rgb(.*)/);
                            wfi_content[i].className = 'wfi_style_color_' + fullColorHex(color[1]);
                            wfi_content[i].innerHTML = wfi_content[i].children[0].innerHTML;
                            for (var n = 0; n < body.getChildCount(); n++) {
                                if (wfi_content[i].className === body.getChild(n).$.className) {
                                    range.selectNodeContents( body.getChild(n) );
                                    selection.selectRanges( [ range ] );
                                }
                            }

                            innerChanged = true;
                        }

                        if (!wfi_content[i].className.match(/wfi_style_color_(.*)/)) {
                            console.log('set parent color')
                            var color = parent_style.color.match(/rgb(.*)/);
                            wfi_content[i].className = 'wfi_style_color_' + fullColorHex(color[1]);
                        }
                    }

                    if (parent_style.backgroundColor) {
                        console.log('parent bg')
                        var color = parent_style.backgroundColor.match(/rgb(.*)/);
                        wfi_content[i].className = 'wfi_style_bgcolor_' + fullColorHex(color[1]);
//                        for (var n = 0; n < body.getChildCount(); n++) {
//                            if (wfi_content[i].className === body.getChild(n).$.className) {
//                                range.selectNodeContents( body.getChild(n) );
//                                selection.selectRanges( [ range ] );
//                            }
//                        }
                    }

                } else if (!parent_style[0] && !wfi_content[i].className.match(/fa fa-(.*)/) && !(wfi_content[i].localName === 'img')) {
                    console.log('no parent style or fa')
                    wfi_content[i].className = '';
                }

                innerChanged = false;
            }
        });
    }

    // Compute the Icon and set the color and create new elements for background color
    function computeIcon(wfi_content, iconHelper) {
        console.log('computeIcon')
        var body = iconHelper.getBody();
        for (var i = 0; i < wfi_content.length; i++) {
            console.log('parent')
            if (wfi_content[i].children.length) {
                console.log('children')
                var wfi_content_children = wfi_content[i].children;
                for (var j = 0; j < wfi_content_children.length; j++) {
                    if (wfi_content_children[j].children.length) {
                        console.log('grandchildren')
                        var wfi_content_grandchildren = wfi_content_children[j].children;
                        for (var k = 0; k < wfi_content_grandchildren.length; k++) {
                            if (wfi_content_grandchildren[k].children.length) {
                                var wfi_content_grandchildren_deep = wfi_content_grandchildren[k].children;
                                for (var l = 0; l < wfi_content_grandchildren_deep.length; l++) {
                                    console.log('deep grandchildren')

                                    // Set icon to uneditable (no Text in span tag allowed)
                                    if (wfi_content_grandchildren_deep[l].className.match(/fa fa-(.*)/)) {
                                        console.log('child grandchild deep')
                                        setIconUneditable(wfi_content_grandchildren_deep[l]);
                                    }

                                    // Deletes Background Color from Icon and inserts new elements
                                    if (wfi_content_grandchildren_deep[l].style.backgroundColor) {
                                        console.log('icon child grandchild deep bg')
                                        computeIconBackgroundColor(wfi_content_grandchildren_deep[l], iconHelper);
                                    }
                                }
                            }
                            if (wfi_content_children[j].className.match(/fa fa-(.*)/)) {
                                console.log('icon child')
                                if (wfi_content_grandchildren[k].style.color) {
                                    console.log('iocn child color')
                                    wfi_content_grandchildren[k].innerHTML = '<span class="' + wfi_content_children[j].className + '" contentEditable="false"></span> ';
                                    wfi_content_children[j].className = '';
                                    wfi_content_children[j].id = 'wfi_toRemove';
                                } else if (wfi_content_grandchildren[k].style.backgroundColor) {
                                    console.log('iocn child bg')
                                    wfi_content_children[j].innerHTML = '<span class="' + wfi_content_children[j].className + '" contentEditable="false">';
                                    wfi_content_children[j].className = '';
                                    wfi_content_children[j].id = 'wfi_toRemove';
                                }
                            }

                            // Set icon to uneditable (no Text in span tag allowed)
                            if (wfi_content_grandchildren[k].className.match(/fa fa-(.*)/)) {
                                console.log('child grandchild')
                                setIconUneditable(wfi_content_grandchildren[k]);
                            }

                            // Deletes Background Color from Icon and inserts new elements
                            if (wfi_content_grandchildren[k].style.backgroundColor) {
                                console.log('icon child grandchild bg')
                                computeIconBackgroundColor(wfi_content_grandchildren[k], iconHelper);
                            }

                        }

                        // if icon exists before switch color or remove background color
                        if (wfi_content_children[j].id === 'wfi_toRemove') {
                            var element = iconHelper.getById('wfi_toRemove');
                            if (wfi_content_children[j].children[0].style.color) {
                                console.log('icon child color')
                                var tmp = wfi_content_children[j].innerHTML;
                                wfi_content_children[j].outerHTML = tmp;
                            } else if (wfi_content_children[j].children[0].className.match(/fa fa-(.*)/)) {
                                console.log('icon child bg')
                                var tmpIcon = CKEDITOR.dom.element.createFromHtml(wfi_content_children[j].children[0].outerHTML);
                                tmpIcon.replace(element);
                            }
                        }

                    }

                    // if icon exists before color or background color
                    if (wfi_content[i].className.match(/fa fa-(.*)/)) {
                        console.log('icon parent')
                        if (wfi_content_children[j].style.color) {
                            console.log('icon parent color')
                            wfi_content_children[j].innerHTML = '<span class="' + wfi_content[i].className + '" contentEditable="false"></span> ';
                            wfi_content[i].className = '';
                            wfi_content[i].id = 'wfi_toRemove_ParentIcon';
                        } else if (wfi_content_children[j].style.backgroundColor) {
                            console.log('icon parent bg')
                            wfi_content[i].innerHTML = '<span class="' + wfi_content[i].className + '" contentEditable="false">';
                            wfi_content[i].className = '';
                            wfi_content[i].id = 'wfi_toRemove_ParentIcon';
                        }
                    }

                    // Set icon to uneditable (no Text in span tag allowed)
                    if (wfi_content_children[j].className.match(/fa fa-(.*)/)) {
                        console.log('parent child')
                        setIconUneditable(wfi_content_children[j]);
                    }

                    // Deletes Background Color from Icon and inserts new elements
                    if (wfi_content_children[j].style.backgroundColor) {
                        console.log('icon grandchild bg')
                        computeIconBackgroundColor(wfi_content_children[j], iconHelper);
                    }
                }

                // if icon exists before switch color or remove background color
                if (wfi_content[i].id === 'wfi_toRemove_ParentIcon') {
                    var element = iconHelper.getById('wfi_toRemove_ParentIcon');
                    if (wfi_content[i].children[0].style.color) {
                        console.log('icon color')
                        var tmp = wfi_content[i].innerHTML;
                        wfi_content[i].outerHTML = tmp;
                    } else if (wfi_content[i].children[0].className.match(/fa fa-(.*)/)) {
                        console.log('icon bg')
                        var tmpIcon = CKEDITOR.dom.element.createFromHtml(wfi_content[i].children[0].outerHTML);
                        tmpIcon.replace(element);
                    }
                }
            }

            // Set icon to uneditable (no Text in span tag allowed)
            if (wfi_content[i].className.match(/fa fa-(.*)/)) {
                console.log('parent parent')
                setIconUneditable(wfi_content[i]);
            }

            // Deletes Background Color from Icon and inserts new elements
            if (wfi_content[i].style.backgroundColor) {
                console.log('icon parent bg')
                computeIconBackgroundColor(wfi_content[i], iconHelper);
            }
        }
        console.log('-------------------------------------------')
    };

    // Set icon to uneditable (no Text in span tag allowed)
    function setIconUneditable (wfi_content) {
        console.log('setIconUneditable')
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
        console.log('computeIconBackgroundColor')
        var color = wfi_content.style.backgroundColor.match(/rgb(.*)/);
        if (wfi_content.childNodes.length === 2) {
            wfi_content.id = 'wfi_toReplace';
            var element = iconHelper.getById('wfi_toReplace');
            var tmpNode1 = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.className + '" style="background-color:#' + fullColorHex(color[1]) + ';">' + wfi_content.childNodes[0].nodeValue + '</span>');
            var tmpNodeIcon = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.childNodes[1].className + '" contentEditable="false"></span> ');
            tmpNode1.replace(element);
            tmpNodeIcon.insertAfter(tmpNode1);
        } else if (wfi_content.childNodes.length === 3) {
            wfi_content.id = 'wfi_toReplace';
            var element = iconHelper.getById('wfi_toReplace');
            var tmpNode1 = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.className + '" style="background-color:#' + fullColorHex(color[1]) + ';">' + wfi_content.childNodes[0].nodeValue + '</span>');
            var tmpNodeIcon = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.childNodes[1].className + '" contentEditable="false"></span> ');
            var tmpNode2 = CKEDITOR.dom.element.createFromHtml('<span class="' + wfi_content.className + '" style="background-color:#' + fullColorHex(color[1]) + ';">' + wfi_content.childNodes[2].nodeValue + '</span>');
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
                        console.log('jquery')
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



