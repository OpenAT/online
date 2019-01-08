CKEDITOR.dialog.add( 'imageUploadDialog', function( editor ) {
    return {
        title: 'Image Upload',
        width: 400,
        height: 300,
        contents: [
            {
                id: 'wfi_image_upload',
                label: 'Upload Image',
                elements: [
                    {
                        id: 'wfi-html-img-sel',
                        type: 'html',
                        html: '<div>Select Image:<form><input id="wfi-img-sel" type="file" name="sel_file"></form></div>',
                        onChange: function() {
                            console.log('test');
                            console.log(this);
//                            // Check for the various File API support.
//                            if (window.File && window.FileReader && window.FileList && window.Blob) {
//                              // Great success! All the File APIs are supported.
//                              console.log('filereader');
//                              var selectedImg = document.getElementById("wfi-img-sel").files[0];
//                              console.log(selectedImg);
//                            } else {
//                              alert('The File APIs are not fully supported in this browser.');
//                            }

//                            document.getElementById("wfi-img-sel").addEventListener("change", website_forum_edit.myFunction);
                            var imgUp = document.getElementById("wfi-img-sel").files[0];
                            console.log('change handleFiles');
                            console.log(imgUp);

                            var img = document.createElement("img");
                            img.classList.add("obj");
                            img.file = imgUp;
                            img.setAttribute("id", "myImg");
//                            img.style.display = 'none';
                            img.style.width = '350px';
                            img.style.height = '220px';

                            var preview = document.getElementById("preview");
                            console.log(preview);
                            preview.appendChild(img); // Assuming that "preview" is the div output where the content will be displayed.

                            var reader = new FileReader();
                            reader.onload = (function(aImg) { return function(e) { aImg.src = e.target.result; }; })(img);
                            reader.readAsDataURL(imgUp);

                        },
                    },

//                    {
//                        id: 'wfi-img-sel',
//                        label: 'Select Image',
//                        type: 'file',
//                        onChange: function( api ) {
////                            console.log(document.getElementsByNamegetElementsByName('wfi-img-sel'));
//                            console.log($( "input[name*='wfi-img-sel']" ));
////                            console.log(CKEDITOR.dialog.getContentElement('wfi-img-up', 'wfi-img-sel'));
//                            // this = CKEDITOR.ui.dialog.select
////                            alert( 'Current value: ' + this.getValue() );
////                        this.getContentElement( 'tab1', 'textareaId' );
//                        }
//                    },
//                    {
//                        type: 'button',
//                        id: 'wfi-img-up',
//                        label: 'Upload Image',
//                        'for': [ 'wfi_image_upload', 'wfi-img-sel' ],
//                        onClick: function(fileUrl, data) {
//                            console.log(this);
//                            console.log(document.getElementsByName('wfi-img-sel')[0].value);
//
////                            onSelect: function( fileUrl, data ) {
////                                alert( 'Successfully uploaded: ' + fileUrl );
////                            }
//                        }
//                    },
                    {
                        id: 'wfi-img-prev',
                        label: 'Image Preview',
                        type: 'html',
                        html: '<div id="preview"></div>'

                    },
                ]
            },
        ],
        onOk: function() {

//            var dialog = this;
//
//            var abbr = editor.document.createElement( 'abbr' );
//            abbr.setAttribute( 'title', dialog.getValueOf( 'tab-basic', 'title' ) );
//            abbr.setText( dialog.getValueOf( 'tab-basic', 'abbr' ) );
//
//            var id = dialog.getValueOf( 'tab-adv', 'id' );
//            if ( id )
//                abbr.setAttribute( 'id', id );
//
//            editor.insertElement( abbr );
            var now = new Date();
			// Insert the timestamp into the document.
			editor.insertHtml( 'The current date and time is: <em>' + now.toString() + '</em>' );
        }
    };
});
