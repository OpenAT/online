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
                        id: 'wfi_html_img_sel',
                        type: 'html',
                        html: '<div>Select Image:<form><input id="wfi_img_sel" type="file" name="sel_file"></form></div>',
                        onChange: function() {
                            console.log('test');
//                            ------------------------------------------------------------------------------------------
                            console.log('canvas');
                            var img = new Image();
                            img.onload = function() {
                                var canvas = document.getElementById('wfi_img_prev_canvas');
                                var ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0, 350, 220);
//                                document.getElementById('wfi_img_resize_width').setAttribute('value', img.width);
//                                document.getElementById('wfi_img_resize_width').setAttribute('max', img.width);
//                                document.getElementById('wfi_img_resize_height').setAttribute('value', img.height);
//                                document.getElementById('wfi_img_resize_height').setAttribute('max', img.height);
                            }
                            img.src = URL.createObjectURL(document.getElementById("wfi_img_sel").files[0]);
                            editor.wfi_image = img;
//                            ------------------------------------------------------------------------------------------

//                            ------------------------------------------------------------------------------------------
//                            console.log("img");
//                            var imgUp = document.getElementById("wfi_img_sel").files[0];
//                            console.log('change handleFiles');
//                            console.log(imgUp);
//
//                            var img = document.createElement("img");
//                            img.classList.add("obj");
//                            img.file = imgUp;
//                            img.setAttribute("id", "myImg");
//                            img.style.width = '350px';
//                            img.style.height = '220px';
//                            editor.wfi_image = img;
//
//                            var preview = document.getElementById("wfi_img_prev");
//                            console.log(preview);
//                            preview.appendChild(img); // Assuming that "preview" is the div output where the content will be displayed.
//
//                            var reader = new FileReader();
//                            reader.onload = (function(aImg) { return function(e) { aImg.src = e.target.result; }; })(img);
//                            reader.readAsDataURL(imgUp);
//                            console.log(reader);
//                            ------------------------------------------------------------------------------------------

                        },
                    },
//                    {
//                        id: 'wfi_img_resize',
//                        label: 'Image Resize',
//                        type: 'html',
//                        html: '<div id="wfi_img_resize">Width: <input type="number" id="wfi_img_resize_width" value="0" min="0">Height: <input type="number" id="wfi_img_resize_height" value="0" min="0"></div>',
//                        onChange: function() {
//                            console.log('input width/height onchange');
////                            var curWidth = $('#wfi_img_resize_width').val();
////                            var curHeight = $('#wfi_img_resize_height').val();
////                            console.log(curWidth);
////                            console.log(curHeight);
//                        }
//                    },
                    {
                        id: 'wfi_img_prev',
                        label: 'Image Preview',
                        type: 'html',
//                        html: '<div id="wfi_img_prev"></div>'
                        html: '<div id="wfi_img_prev"><canvas id="wfi_img_prev_canvas" style="width: 350px; height:220px;"></canvas></div>'

                    },
                ]
            },
        ],
        onOk: function() {
            console.log('onOk');
            console.log(editor.wfi_image);
            console.log(editor.wfi_image.width);
            console.log(editor.wfi_image.height);
            console.log(editor.wfi_image.src);
//                            ------------------------------------------------------------------------------------------
            console.log('canvas');
            var wfiImg = editor.wfi_image;
            var canvas = document.getElementById('wfi_img_prev_canvas');
            console.log(canvas);
            var tmpImg = new Image();
            tmpImg.src = canvas.toDataURL();
            console.log(wfiImg);

            tmpImg.onload = function() {
                canvas.width = wfiImg.width;
                canvas.height = wfiImg.height;
                console.log(canvas.width);
                console.log(canvas.height);
                var ctx = canvas.getContext('2d');
                ctx.drawImage(tmpImg, 0, 0, wfiImg.width, wfiImg.height);

                var uri = canvas.toDataURL();
//                function toBlob(dataURI) {
//                    var byteString = atob(dataURI.split(',')[1]);
//                    var ab = new ArrayBuffer(byteString.length);
//                    var ia = new Uint8Array(ab);
//                    for (var i = 0; i < byteString.length; i++) {
//                        ia[i] = byteString.charCodeAt(i);
//                    }
//                    return new Blob([ab], { type: 'image/png' });
//                }
//                var blob = toBlob(uri);
//                console.log(blob);
//                var blobToFile = new File([blob], 'newImg', {type: blob.type, lastModified: Date.now()});
//                console.log(blobToFile);
                editor.insertHtml('<img src="' + uri + '">');
            }


//                            ------------------------------------------------------------------------------------------
//            console.log('image');
//            var imgIn = document.getElementById('myImg');
//            editor.insertHtml('<img src="' + imgIn.src + '">');
//            console.log(imgIn);
//                            ------------------------------------------------------------------------------------------

//                            ------------------------------------------------------------------------------------------
//            var canvas = self.darkroom.canvas;
//            var lowerCanvas = canvas.lowerCanvasEl;
//            var darkroomImg = self.darkroom.image;
//            var tmpImg = new Image();
//            tmpImg.src = lowerCanvas.toDataURL();
//
//            tmpImg.onload = function() {
//                lowerCanvas.width = darkroomImg.width;
//                lowerCanvas.height = darkroomImg.height;
//                var lowerCanvasCtx = lowerCanvas.getContext('2d')
//                lowerCanvasCtx.drawImage(tmpImg, 0, 0, darkroomImg.width, darkroomImg.height);
//
//                var uri = lowerCanvas.toDataURL();
//                var blob = self.dataURItoBlob(uri);
//                var blobToFile = new File([blob], imgText, {type: blob.type, lastModified: Date.now()});
//                self.make_request(blobToFile);
//            }
//
//        },
//
//        dataURItoBlob: function(dataURI) {
//            var byteString = atob(dataURI.split(',')[1]);
//            var ab = new ArrayBuffer(byteString.length);
//            var ia = new Uint8Array(ab);
//            for (var i = 0; i < byteString.length; i++) {
//                ia[i] = byteString.charCodeAt(i);
//            }
//            return new Blob([ab], { type: 'image/png' });
//        },
//                            ------------------------------------------------------------------------------------------

//            var img = editor.document.createElement('img');
//            abbr.setAttribute( 'title', dialog.getValueOf( 'tab-basic', 'title' ) );
//            abbr.setText( dialog.getValueOf( 'tab-basic', 'abbr' ) );
//
//            var id = dialog.getValueOf( 'tab-adv', 'id' );
//            if ( id )
//                abbr.setAttribute( 'id', id );
//
//            editor.insertElement( abbr );
//            var now = new Date();
			// Insert the timestamp into the document.
//			editor.insertHtml( '<img src="' + now.toString() + '"></img>' );
//            editor.insertHtml(editor.wfi_image);
        }
    };
});
