/// <reference path='/../lib/darkroomjs/lib/core/darkroom.js'/>

CKEDITOR.plugins.add( 'imageupload', {

	icons: 'imageupload',

	init: function( editor ) {

		editor.addCommand( 'imageUpload', new CKEDITOR.dialogCommand('imageUploadDialog'));

		editor.ui.addButton( 'ImageUpload', {
			label: 'Upload Image',
			command: 'imageUpload',
			toolbar: 'special'
		});

		editor.wfi_image = {};

		CKEDITOR.dialog.add( 'imageUploadDialog', '/website_forum_imagedialog/static/src/js/myplugins/imageupload/dialogs/imageupload.js');
	}
});
