/// <reference path='/../lib/darkroomjs/lib/core/darkroom.js'/>

(function () {
    'use strict';

    var website = openerp.website;
    var _t = openerp._t;
    var webEditor = website.editor;

    var IMAGES_PER_ROW = 6;
    var IMAGES_ROWS = 2;
    webEditor.ImageDialog.include({
        events: {
            //--------------------------------------
            // all ImageDialog events
            'change .url-source': function (e) {
                this.changed($(e.target));
            },
            'click button.filepicker': function () {
                var filepicker = this.$('input[type=file]');
                if (!_.isEmpty(filepicker)){
                    filepicker[0].click();
                }
            },
            'click .js_disable_optimization': function () {
                this.$('input[name="disable_optimization"]').val('1');
                var filepicker = this.$('button.filepicker');
                if (!_.isEmpty(filepicker)){
                    filepicker[0].click();
                }
            },
            'change input[type=file]': 'file_selection',
            'submit form': 'form_submit',
            'change input.url': "change_input",
            'keyup input.url': "change_input",
            //'change select.image-style': 'preview_image',
            'click .existing-attachments img': 'select_existing',
            'click .existing-attachment-remove': 'try_remove',
            //--------------------------------------
            'click .tryEdit': 'try_edit',
            'click .closeEdit': 'close_edit',
            'click .saveEdit': 'save_edit',

        },
        //----------------------------------------------------
        // Solution for foreach problem in xml file
        init: function (field_manager, node) {
            this._super(field_manager, node);
            //change rows to other name accordingly to foreach varname
            this.rows = [];
            this.darkroom = {};

        },
        //----------------------------------------------------

        display_attachments: function() {
            // necessary for foreach problem
            this._super();

            //----------------------------------------------------
            this.$('.help-block').empty();
            var per_screen = IMAGES_PER_ROW * IMAGES_ROWS;

            var from = this.page * per_screen;
            var records = this.records;

            // Create rows of 3 records
            var rows = _(records).chain()
                .slice(from, from + per_screen)
                .groupBy(function (_, index) { return Math.floor(index / IMAGES_PER_ROW); })
                .values()
                .value();

            //----------------------------------------------------
            //set foreach variable
            this.rows = rows;
            //----------------------------------------------------

            this.$('.existing-attachments').replaceWith(
                openerp.qweb.render(
                    'wie_image_editor', {rows: rows}));
            this.parent.$('.pager')
                .find('li.previous').toggleClass('disabled', (from === 0)).end()
                .find('li.next').toggleClass('disabled', (from + per_screen >= records.length));
            //----------------------------------------------------

        },

        try_edit: function(e) {
            var $a = $(e.target);
            var id = parseInt($a.data('id'), 10);
            var image = _.findWhere(this.records, {id: id});

            this.$('.existing-attachments').after(
                openerp.qweb.render(
                    'wie_image_modal', {image: image}
                    ));

            var toEdit = document.getElementById('imageModal');
            toEdit.style.display = 'block';
            var imgToEdit = document.getElementById(image.id);
            this.darkroom = new Darkroom(imgToEdit, {
                backgroundColor: 'transparent',
            });

        },

        close_edit: function() {
            var toClose = document.getElementById('imageModal');
            toClose.style.display = "none";
            $('#imageModal').remove();
            this.display_attachments();
        },

        save_edit: function(e) {
            e.preventDefault();

            var $a = $(e.target);
            var imgId = parseInt($a.data('id'), 10);

            var self = this;

            var imgText =  document.getElementById('imageText').value;

            if (imgText.search('.png') === -1)
            {
                imgText = imgText + '.png';
            }

            var newImg = new Image();
            var canvas = self.darkroom.canvas;
            var lowerCanvas = canvas.lowerCanvasEl;
            var darkroomImg = self.darkroom.image;
            var tmpImg = new Image();
            tmpImg.src = lowerCanvas.toDataURL();


            tmpImg.onload = function() {
                lowerCanvas.width = darkroomImg.width;
                lowerCanvas.height = darkroomImg.height;
                var lowerCanvasCtx = lowerCanvas.getContext('2d')
                lowerCanvasCtx.drawImage(tmpImg, 0, 0, darkroomImg.width, darkroomImg.height);

                var uri = lowerCanvas.toDataURL();
                var blob = self.dataURItoBlob(uri);
                var blobToFile = new File([blob], imgText, {type: blob.type, lastModified: Date.now()});
                self.make_request(blobToFile);

                self.file_selected(uri, null);

            }

        },

        dataURItoBlob: function(dataURI) {
            var byteString = atob(dataURI.split(',')[1]);
            var ab = new ArrayBuffer(byteString.length);
            var ia = new Uint8Array(ab);
            for (var i = 0; i < byteString.length; i++) {
                ia[i] = byteString.charCodeAt(i);
            }
            return new Blob([ab], { type: 'image/png' });
        },

        make_request: function(image) {

            var formData = new FormData();
            formData.append('upload', image, image.name);
            var uid = _.uniqueId('func_');
            formData.append('func', uid);

            //Request
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/website/attach", true);

            xhr.send(formData);
        },

    });

    website.editor.RTEImageDialog.include({
        init: function (parent, editor, media) {
            this._super(parent, editor, media);
            // this.media -> necessary for openening imagedialog with customize->change button
            this.media = media;

            this.on('start', this, this.proxy('started'));
            this.on('save', this, this.proxy('saved'));
        },
    });
})();
