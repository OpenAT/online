CKEDITOR.plugins.add( 'imageupload', {

	icons: 'imageupload',

	init: function( editor ) {

		editor.addCommand( 'imageUpload', new CKEDITOR.dialogCommand('imageUploadDialog'));

		editor.ui.addButton( 'ImageUpload', {
			label: 'Upload Image',
			command: 'imageUpload',
			toolbar: 'insert'
		});

		CKEDITOR.dialog.add( 'imageUploadDialog', '/website_forum_imagedialog/static/src/js/myplugins/imageupload/dialogs/imageupload.js');
	}
});
