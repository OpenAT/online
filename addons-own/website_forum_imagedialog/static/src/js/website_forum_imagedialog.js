openerp.website.if_dom_contains('.website_forum', function () {
    console.log('website forum imagedialog dom contains long');

    CKEDITOR.on('dialogDefinition', function(ev) {
    // Take the dialog window name and its definition from the event data.
        var dialogName = ev.data.name;
        var dialogDefinition = ev.data.definition;
        var dialog = CKEDITOR.dialog.getCurrent();

        console.log(ev.editor.plugins.filebrowser);
        console.log(ev.data.definition);

//        var definition = ev.data.definition;
//		var element;
		// Associate filebrowser to elements with 'filebrowser' attribute.
//		for (var i = 0; i < definition.contents.length; ++i) {
//			if ((element = definition.contents[i])) {
//				attachFileBrowser(ev.editor, ev.data.name, definition, element.elements);
//				if (element.hidden && element.filebrowser)
//					element.hidden = !isConfigured(definition, element.id, element.filebrowser);
//
//			}
//		}
//        dialogDefinition.onLoad = function () {
//            console.log('afterInit');
//            $('td.cke_dialog_ui_hbox_last').first().replaceWith(
//                openerp.qweb.render(
//                'wfi_imageDialog'
//            ));
//
//            $('#wfi_input').on('click', function(e) {
//                console.log('on click test');
//                console.log($(this).val(''));
//            });
//
//            $('#wfi_input').change(function(e) {
//                console.log('on change test');
//                console.log(e);
//                var wfi_upload = e.currentTarget;
//                console.log(wfi_upload);
//                console.log(wfi_upload.value);
//
//                var tmppath = URL.createObjectURL(e.target.files[0]);
////                $("img").fadeIn("fast").attr('src',URL.createObjectURL(e.target.files[0]));
////                $("#disp_tmp_path").html("Temporary Path(Copy it and try pasting it in browser address bar) --> <strong>["+tmppath+"]</strong>");
//                console.log(tmppath);
//            });
//        };
//        dialogDefinition.onShow = function () {
//            console.log('dialogDefinition test');
//            $('td.cke_dialog_ui_hbox_last').first().replaceWith(
//                openerp.qweb.render(
//                'wfi_imageDialog'
//            ));
//
//            $('#wfi_input').on('click', function(e) {
//                console.log('on click test');
//                console.log($(this).val(''));
//            });
//
//            $('#wfi_input').change(function(e) {
//                console.log('on change test');
//                console.log(e);
//                var wfi_upload = e.currentTarget;
//                console.log(wfi_upload);
//                console.log(wfi_upload.value);
//
//                var tmppath = URL.createObjectURL(e.target.files[0]);
////                $("img").fadeIn("fast").attr('src',URL.createObjectURL(e.target.files[0]));
////                $("#disp_tmp_path").html("Temporary Path(Copy it and try pasting it in browser address bar) --> <strong>["+tmppath+"]</strong>");
//                console.log(tmppath);
//            });
//        };

        if (dialogName == 'image') {
//            dialogDefinition.onShow = function() {
            console.log('image dialog test');
            var infoTab = dialogDefinition.getContents('info');
//            console.log(infoTab);
            // Remove unnecessary widgets
            infoTab.remove( 'ratioLock' );
//            infoTab.remove( 'txtHeight' );
//            infoTab.remove( 'txtWidth' );
            infoTab.remove( 'txtBorder');
            infoTab.remove( 'txtHSpace');
            infoTab.remove( 'txtVSpace');
            infoTab.remove( 'cmbAlign' );

            dialogDefinition.removeContents( 'Link' );
            dialogDefinition.removeContents( 'advanced' );


            var uploadTab = dialogDefinition.getContents( 'Upload' );
            var uploadButton = uploadTab.get( 'uploadButton' );
            uploadButton[ 'label' ] = 'Upload to your Media Gallery';


             // Get a reference to the 'Image Info' tab.
             var infoTab = dialogDefinition.getContents( 'info' );

            // ADD OUR CUSTOM TEXT
            infoTab.add(
              {
                type : 'html',
                html : 'Click the button to select your image from your gallery,<br> or use the UPLOAD tab to upload a new image.'
              },
              'htmlPreview'
            );

            var imageButton = infoTab.get( 'browse' );
            imageButton[ 'label' ] = 'Select Image';
            console.log(imageButton);
//
//            //I HAVE DONE THIS TO HIDE BUT I WOULD LIKE TO REALLY HIDE!
//            var urlField = infoTab.get( 'txtUrl' );
//            urlField[ 'style' ] = 'display:none; width:0;';
//            };

//                infoTab.remove( 'htmlPreview' );

//                var dialog = CKEDITOR.dialog.getCurrent();

//                var elem = dialog.getContentElement('info','htmlPreview');
//                elem.getElement().hide();
//                dialog.hidePage( 'Link' );
//                dialog.hidePage( 'advanced' );
//                dialog.hidePage( 'info' ); // works now (CKEditor v3.6.4)
//                this.selectPage('Upload');

//                dialogDefinition.onShow = function () {
//                    $('td.cke_dialog_ui_hbox_last').first().replaceWith(
//                        openerp.qweb.render(
//                        'wfi_imageDialog'
//                    ));
//
//                    $('#wfi_input').on('click', function(e) {
//                        console.log('on click test');
//                        console.log($(this).val(''));
//                    });
//
//                    $('#wfi_input').change(function(e) {
//                        console.log('on change test');
//                        console.log(e);
//                        var wfi_upload = e.currentTarget;
//                        console.log(wfi_upload);
//                        console.log(wfi_upload.value);
//
//                        var tmppath = URL.createObjectURL(e.target.files[0]);
////                        $("img").fadeIn("fast").attr('src',URL.createObjectURL(e.target.files[0]));
////                        $("#disp_tmp_path").html("Temporary Path(Copy it and try pasting it in browser address bar) --> <strong>["+tmppath+"]</strong>");
//                        console.log(tmppath);
//
//                    });
//                };
//                    var dialog = CKEDITOR.dialog.getCurrent();
//                    var elem = dialog.getContentElement('info','htmlPreview');


//                    elem.getElement().hide();
//
//                    dialog.hidePage( 'Link' );
//                    dialog.hidePage( 'advanced' );
//                    dialog.hidePage( 'info' ); // works now (CKEditor v3.6.4)
//                    this.selectPage('FileBrowser');
//
//                    /*var uploadTab = dialogDefinition.getContents('Upload');
//                    var uploadButton = uploadTab.get('uploadButton');
//                    uploadButton['filebrowser']['onSelect'] = function( fileUrl, errorMessage ) {
//                        //$("input.cke_dialog_ui_input_text").val(fileUrl);
//                        dialog.getContentElement('info', 'txtUrl').setValue(fileUrl);
//                        //$(".cke_dialog_ui_button_ok span").click();
//                    }*/
//                    $('.cke_dialog_ui_hbox_first').first().after(
//                    $('td.cke_dialog_ui_hbox_last').first().replaceWith(
//                        openerp.qweb.render(
//                        'wfi_imageDialog'
//                    ));
//
//
//                    $('#wfi_input').on('click', function(e) {
//                        console.log('on click test');
//                        console.log($(this).val(''));
//                    });
//
//                    $('#wfi_input').change(function(e) {
//                        console.log('on change test');
//                        console.log(e);
//                        var wfi_upload = e.currentTarget;
//                        console.log(wfi_upload);
//                        console.log(wfi_upload.value);
//
//                    });
//                };

//////                $('.cke_dialog_body').replaceWith(
//                $('.cke_dialog_ui_hbox_last').replaceWith(
//                    openerp.qweb.render(
//                    'wfi_imageDialog'
//                ));
////                dialog.hide();
//
////                init_wfi_filepicker();
////                console.log($(".cke_reset_all").css());
////                $('.cke_dialog_ui_vbox_child').remove();
////                $('.cke_dialog_body').remove(); // remove complete body and build own
//                // This code will open the Link tab.
////                this.selectPage( 'Link' );
//                };
        }


    });

//    console.log($('#wfi_input'));
////
////    function wfi_input_function(e) {
////        console.log('on submit test');
////        console.log(e);
////    }
//    $('#wfi_input').change(function(e) {
//        console.log('change test');
//        console.log(e);
//    });




});
//
//openerp.website.if_dom_contains('#wfi_input', function () {
//    console.log('wfi_input existing');
//
//
//    $('#wfi_input').on('click', function(e) {
//        console.log('on click test');
//        console.log($(this).val(''));
//    });
//
//    $('#wfi_input').change(function(e) {
//        console.log('on change test');
//        console.log(e);
//    });
//
//});

