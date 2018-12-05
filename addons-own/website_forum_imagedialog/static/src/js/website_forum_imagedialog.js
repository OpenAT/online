openerp.website.if_dom_contains('.website_forum', function () {
    console.log('website forum imagedialog dom contains long');

    var uniqueNameCounter = 0,
		// Black rectangle which is shown before the image is loaded.
		loadingImage = 'data:image/gif;base64,R0lGODlhDgAOAIAAAAAAAP///yH5BAAAAAAALAAAAAAOAA4AAAIMhI+py+0Po5y02qsKADs=';

	// Returns number as a string. If a number has 1 digit only it returns it prefixed with an extra 0.
	function padNumber( input ) {
		if ( input <= 9 ) {
			input = '0' + input;
		}

		return String( input );
	}

	// Returns a unique image file name.
	function getUniqueImageFileName( type ) {
		var date = new Date(),
			dateParts = [ date.getFullYear(), date.getMonth() + 1, date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds() ];

		uniqueNameCounter += 1;

		return 'image-' + CKEDITOR.tools.array.map( dateParts, padNumber ).join( '' ) + '-' + uniqueNameCounter + '.' + type;
	}

	CKEDITOR.plugins.add( 'uploadimage', {
		requires: 'uploadwidget',

		onLoad: function() {
			CKEDITOR.addCss(
				'.cke_upload_uploading img{' +
					'opacity: 0.3' +
				'}'
			);
		},

		init: function( editor ) {
			// Do not execute this paste listener if it will not be possible to upload file.
			if ( !CKEDITOR.plugins.clipboard.isFileApiSupported ) {
				return;
			}

			var fileTools = CKEDITOR.fileTools,
				uploadUrl = fileTools.getUploadUrl( editor.config, 'image' );

			if ( !uploadUrl ) {
				return;
			}

			// Handle images which are available in the dataTransfer.
			fileTools.addUploadWidget( editor, 'uploadimage', {
				supportedTypes: /image\/(jpeg|png|gif|bmp)/,

				uploadUrl: uploadUrl,

				fileToElement: function() {
					var img = new CKEDITOR.dom.element( 'img' );
					img.setAttribute( 'src', loadingImage );
					return img;
				},

				parts: {
					img: 'img'
				},

				onUploading: function( upload ) {
					// Show the image during the upload.
					this.parts.img.setAttribute( 'src', upload.data );
				},

				onUploaded: function( upload ) {
					// Width and height could be returned by server (https://dev.ckeditor.com/ticket/13519).
					var $img = this.parts.img.$,
						width = upload.responseData.width || $img.naturalWidth,
						height = upload.responseData.height || $img.naturalHeight;

					// Set width and height to prevent blinking.
					this.replaceWith( '<img src="' + upload.url + '" ' +
						'width="' + width + '" ' +
						'height="' + height + '">' );
				}
			} );

			// Handle images which are not available in the dataTransfer.
			// This means that we need to read them from the <img src="data:..."> elements.
			editor.on( 'paste', function( evt ) {
				// For performance reason do not parse data if it does not contain img tag and data attribute.
				if ( !evt.data.dataValue.match( /<img[\s\S]+data:/i ) ) {
					return;
				}

				var data = evt.data,
					// Prevent XSS attacks.
					tempDoc = document.implementation.createHTMLDocument( '' ),
					temp = new CKEDITOR.dom.element( tempDoc.body ),
					imgs, img, i;

				// Without this isReadOnly will not works properly.
				temp.data( 'cke-editable', 1 );

				temp.appendHtml( data.dataValue );

				imgs = temp.find( 'img' );

				for ( i = 0; i < imgs.count(); i++ ) {
					img = imgs.getItem( i );

					// Assign src once, as it might be a big string, so there's no point in duplicating it all over the place.
					var imgSrc = img.getAttribute( 'src' ),
						// Image have to contain src=data:...
						isDataInSrc = imgSrc && imgSrc.substring( 0, 5 ) == 'data:',
						isRealObject = img.data( 'cke-realelement' ) === null;

					// We are not uploading images in non-editable blocs and fake objects (https://dev.ckeditor.com/ticket/13003).
					if ( isDataInSrc && isRealObject && !img.data( 'cke-upload-id' ) && !img.isReadOnly( 1 ) ) {
						// Note that normally we'd extract this logic into a separate function, but we should not duplicate this string, as it might
						// be large.
						var imgFormat = imgSrc.match( /image\/([a-z]+?);/i ),
							loader;

						imgFormat = ( imgFormat && imgFormat[ 1 ] ) || 'jpg';

						loader = editor.uploadRepository.create( imgSrc, getUniqueImageFileName( imgFormat ) );
						loader.upload( uploadUrl );

						fileTools.markElement( img, 'uploadimage', loader.id );

						fileTools.bindNotifications( editor, loader );
					}
				}

				data.dataValue = temp.getHtml();
			} );
		}
	} );


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

        if (dialogName == 'image') {
//            dialogDefinition.onShow = function() {
                console.log('click test');
                var infoTab = dialogDefinition.getContents('info');
                console.log(infoTab);
                // Remove unnecessary widgets
                infoTab.remove( 'ratioLock' );
//                infoTab.remove( 'txtHeight' );
//                infoTab.remove( 'txtWidth' );
                infoTab.remove( 'txtBorder');
                infoTab.remove( 'txtHSpace');
                infoTab.remove( 'txtVSpace');
                infoTab.remove( 'cmbAlign' );
                var tes = CKEDITOR.instances['image'];
                console.log(tes);
//                tes.setValue('asdfasbgfb');
//                infoTab.remove( 'htmlPreview' );


//                var btnTest = '<button onclick="returnFileUrl()">Select File</button>';
//                $('td.cke_dialog_ui_hbox_last').replaceWith('<button onclick="returnFileUrl()">Select File</button>');
//                var dialog = CKEDITOR.dialog.getCurrent();

//                var elem = dialog.getContentElement('info','htmlPreview');
//                elem.getElement().hide();
//                dialog.hidePage( 'Link' );
//                dialog.hidePage( 'advanced' );
//                dialog.hidePage( 'info' ); // works now (CKEditor v3.6.4)
//                this.selectPage('Upload');
                dialogDefinition.onShow = function () {
                    var dialog = CKEDITOR.dialog.getCurrent();
//
                    var elem = dialog.getContentElement('info','htmlPreview');


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
                    $('td.cke_dialog_ui_hbox_last').first().replaceWith(
                        openerp.qweb.render(
                        'wfi_imageDialog'
                    ));
                    var newURL = 'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/5cb38afa-bb36-4027-adbb-db659613c16a/dct0nrw-36b5f309-502c-4cf5-be88-a3cb0f19eea5.jpg/v1/fill/w_1280,h_800,q_70,strp/would_you_remember__by_lightdrop_dct0nrw-fullview.jpg';
//                    dialog.setValueOf('info', 'txtUrl', newURL);
                };

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

//    function attachFileBrowser(editor, dialogName, definition, elements) {
//		if (!elements || !elements.length)
//			return;
//
//		var element;
//
//		for (var i = elements.length; i--;) {
//			element = elements[i];
//
//			if (element.type == 'hbox' || element.type == 'vbox' || element.type == 'fieldset')
//				attachFileBrowser(editor, dialogName, definition, element.children);
//
//			if (!element.filebrowser)
//				continue;
//
//			if (typeof element.filebrowser == 'string') {
//				var fb = {
//					action: (element.type == 'fileButton') ? 'QuickUpload' : 'Browse',
//					target: element.filebrowser
//				};
//				element.filebrowser = fb;
//			}
//
//			if (element.filebrowser.action == 'Browse') {
//				var url = element.filebrowser.url;
//				if (url === undefined) {
//					url = editor.config['filebrowser' + ucFirst(dialogName) + 'BrowseUrl'];
//					if (url === undefined)
//						url = editor.config.filebrowserBrowseUrl;
//				}
//
//				if (url) {
//					element.onClick = browseServer;
//					element.filebrowser.url = url;
//					element.hidden = false;
//				}
//			} else if (element.filebrowser.action == 'QuickUpload' && element['for']) {
//				url = element.filebrowser.url;
//				if (url === undefined) {
//					url = editor.config['filebrowser' + ucFirst(dialogName) + 'UploadUrl'];
//					if (url === undefined)
//						url = editor.config.filebrowserUploadUrl;
//				}
//
//				if (url) {
//					var onClick = element.onClick;
//
//					// "element" here means the definition object, so we need to find the correct
//					// button to scope the event call
//					element.onClick = function(ev) {
//						var sender = ev.sender,
//							fileInput = sender.getDialog().getContentElement(this['for'][0], this['for'][1]).getInputElement(),
//							isFileUploadApiSupported = CKEDITOR.fileTools && CKEDITOR.fileTools.isFileUploadSupported;
//
//						if (onClick && onClick.call(sender, ev) === false) {
//							return false;
//						}
//
//						if (uploadFile.call(sender, ev)) {
//							// Use one of two upload strategies, either form or XHR based (#643).
//							if (editor.config.filebrowserUploadMethod === 'form' || !isFileUploadApiSupported) {
//								// Append token preventing CSRF attacks.
//								appendToken(fileInput);
//								return true;
//							} else {
//								var loader = editor.uploadRepository.create(fileInput.$.files[0]);
//
//								loader.on('uploaded', function(ev) {
//									var response = ev.sender.responseData;
//									setUrl.call(ev.sender.editor, response.url, response.message);
//								});
//
//								// Return non-false value will disable fileButton in dialogui,
//								// below listeners takes care of such situation and re-enable "send" button.
//								loader.on('error', xhrUploadErrorHandler.bind(this));
//								loader.on('abort', xhrUploadErrorHandler.bind(this));
//
//								loader.loadAndUpload(addMissingParams(url));
//
//								return 'xhr';
//							}
//						}
//						return false;
//					};
//
//					element.filebrowser.url = url;
//					element.hidden = false;
//					setupFileElement(editor, definition.getContents(element['for'][0]).get(element['for'][1]), element.filebrowser);
//				}
//			}
//		}
//	}
//
//	function ucFirst(str) {
//		str += '';
//		var f = str.charAt(0).toUpperCase();
//		return f + str.substr(1);
//	}
//
//    function uploadFile() {
//            var dialog = this.getDialog();
//            var editor = dialog.getParentEditor();
//
//            editor._.filebrowserSe = this;
//
//            // If user didn't select the file, stop the upload.
//            if (!dialog.getContentElement(this['for'][0], this['for'][1]).getInputElement().$.value)
//                return false;
//
//            if (!dialog.getContentElement(this['for'][0], this['for'][1]).getAction())
//                return false;
//
//            return true;
//	}
//
//    function setUrl(fileUrl, data) {
//		var dialog = this._.filebrowserSe.getDialog(),
//			targetInput = this._.filebrowserSe['for'],
//			onSelect = this._.filebrowserSe.filebrowser.onSelect;
//
//		if (targetInput)
//			dialog.getContentElement(targetInput[0], targetInput[1]).reset();
//
//		if (typeof data == 'function' && data.call(this._.filebrowserSe) === false)
//			return;
//
//		if (onSelect && onSelect.call(this._.filebrowserSe, fileUrl, data) === false)
//			return;
//
//		// The "data" argument may be used to pass the error message to the editor.
//		if (typeof data == 'string' && data)
//			alert(data); // jshint ignore:line
//
//		if (fileUrl)
//			updateTargetElement(fileUrl, this._.filebrowserSe);
//	}
//
//	function updateTargetElement(url, sourceElement) {
//		var dialog = sourceElement.getDialog();
//		var targetElement = sourceElement.filebrowser.target || null;
//
//		// If there is a reference to targetElement, update it.
//		if (targetElement) {
//			var target = targetElement.split(':');
//			var element = dialog.getContentElement(target[0], target[1]);
//			if (element) {
//				element.setValue(url);
//				dialog.selectPage(target[0]);
//			}
//		}
//	}
//
//    function appendToken(fileInput) {
//		var tokenElement;
//		var form = new CKEDITOR.dom.element(fileInput.$.form);
//
//		if (form) {
//			// Check if token input element already exists.
//			tokenElement = form.$.elements['ckCsrfToken'];
//
//			// Create new if needed.
//			if (!tokenElement) {
//				tokenElement = new CKEDITOR.dom.element('input');
//				tokenElement.setAttributes( {
//					name: 'ckCsrfToken',
//					type: 'hidden'
//				} );
//
//				form.append(tokenElement);
//			} else {
//				tokenElement = new CKEDITOR.dom.element(tokenElement);
//			}
//
//			tokenElement.setAttribute('value', CKEDITOR.tools.getCsrfToken());
//		}
//	}
//
//    function isConfigured(definition, tabId, elementId) {
//		if (elementId.indexOf(';') !== -1) {
//			var ids = elementId.split(';');
//			for (var i = 0; i < ids.length; i++) {
//				if (isConfigured(definition, tabId, ids[i]))
//					return true;
//			}
//			return false;
//		}
//
//		var elementFileBrowser = definition.getContents(tabId).get(elementId).filebrowser;
//		return (elementFileBrowser && elementFileBrowser.url);
//	}
//
//	function addMissingParams(url) {
//		if (!url.match(/command=QuickUpload/) || url.match(/(\?|&)responseType=json/)) {
//			return url;
//		}
//
//		return addQueryString(url, {responseType: 'json'});
//	}
//
//    function addQueryString(url, params) {
//		var queryString = [];
//
//		if (!params)
//			return url;
//		else {
//			for (var i in params)
//				queryString.push(i + '=' + encodeURIComponent(params[i]));
//		}
//
//		return url + ((url.indexOf('?') != -1) ? '&' : '?') + queryString.join('&');
//	}
//
//    function browseServer() {
//		var dialog = this.getDialog();
//		var editor = dialog.getParentEditor();
//
//		editor._.filebrowserSe = this;
//
//		var width = editor.config['filebrowser' + ucFirst(dialog.getName()) + 'WindowWidth'] || editor.config.filebrowserWindowWidth || '80%';
//		var height = editor.config['filebrowser' + ucFirst(dialog.getName()) + 'WindowHeight'] || editor.config.filebrowserWindowHeight || '70%';
//
//		var params = this.filebrowser.params || {};
//		params.CKEditor = editor.name;
//		params.CKEditorFuncNum = editor._.filebrowserFn;
//		if (!params.langCode)
//			params.langCode = editor.langCode;
//
//		var url = addQueryString(this.filebrowser.url, params);
//		// TODO: V4: Remove backward compatibility (https://dev.ckeditor.com/ticket/8163).
//		editor.popup(url, width, height, editor.config.filebrowserWindowFeatures || editor.config.fileBrowserWindowFeatures);
//	}
//
//    function setupFileElement(editor, fileInput, filebrowser) {
//		var params = filebrowser.params || {};
//		params.CKEditor = editor.name;
//		params.CKEditorFuncNum = editor._.filebrowserFn;
//		if (!params.langCode)
//			params.langCode = editor.langCode;
//
//		fileInput.action = addQueryString(filebrowser.url, params);
//		fileInput.filebrowser = filebrowser;
//	}
//
//    function xhrUploadErrorHandler(ev) {
//		var response = {};
//
//		try {
//			response = JSON.parse(ev.sender.xhr.response) || {};
//		} catch (e) {}
//
//		// `this` is a reference to ui.dialog.fileButton.
//		this.enable();
//		alert(response.error ? response.error.message : ev.sender.message); // jshint ignore:line
//	}
});
