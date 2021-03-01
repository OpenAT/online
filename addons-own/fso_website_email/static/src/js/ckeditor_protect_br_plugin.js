(function () {
    'use strict';

    CKEDITOR.plugins.add('brangel', {
        init: function (editor) {
            editor.on('toHtml', function (evt) {
                protectBRs(evt.data.dataValue);
            }, null, null, 5);
            editor.on('toHtml', function (evt) {
                unprotectBRs(evt.data.dataValue);
            }, null, null, 14);
            editor.on('toDataFormat', function (evt) {
                protectBRs(evt.data.dataValue);
            }, null, null, 5);
            editor.on('toDataFormat', function (evt) {
                unprotectBRs(evt.data.dataValue);
            }, null, null, 14);

            function protectBRs(element) {
                var children = element.children;
                if (children) {
                    for (var i = children.length; i--;) {
                        var child = children[i];
                        if (child.name == "br") {
                            var placeholder = new CKEDITOR.htmlParser.text('{cke_br}');
                            placeholder.insertAfter(child);
                            child.remove();
                        } else {
                            protectBRs(child);
                        }
                    }
                }
            }

            function unprotectBRs(element) {
                var children = element.children;
                if (children) {
                    for (var i = children.length; i--;) {
                        var child = children[i];
                        if (child instanceof CKEDITOR.htmlParser.text && child.value === "{cke_br}") {
                            var br = new CKEDITOR.htmlParser.element('br');
                            br.insertAfter(child);
                            child.remove();
                        } else {
                            unprotectBRs(child);
                        }
                    }
                }
            }
        }
    });

})();
