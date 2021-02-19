(function () {
    'use strict';

    openerp.website.editor.RTEImageDialog = openerp.website.editor.RTEImageDialog.extend({
        start: function () {
            console.log('ImageDialog start()', this.media);
            $('input#input_img_alt_text').val($(this.media).attr('alt'))
            return this._super();
        },
        select_existing: function (e) {
            console.log('ImageDialog select_existing():', this);
            var link = $(e.currentTarget).attr('src');
            if (link) {
                $('#wedi_selected_image').attr('src', link);
            }
            return this._super(e);
        },
        selected_existing: function (link) {
            console.log('ImageDialog selected_existing():', this);
            return this._super(link);
        },
        set_image: function (url, error) {
            console.log('ImageDialog set_image():', this);
            if (url) $('#wedi_selected_image').attr('src', url);
            return this._super(url, error);
        },
        save: function () {
            console.log('ImageDialog save():', this);
            $(this.media).attr('alt', $('input#input_img_alt_text').val());
            return this._super()
        }
    });

})();
