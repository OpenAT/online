(function() {
'use strict';

    var Mirror = Darkroom.Transformation.extend({
        applyTransformation: function(canvas, image, next) {
            if (this.options.XorY === 'X')
            {
                image.setFlipX(!image.getFlipX());
            }
            else if (this.options.XorY === 'Y')
            {
                image.setFlipY(!image.getFlipY());
            }
            next();
        },
    });

    Darkroom.plugins['mirror'] = Darkroom.Plugin.extend({

        initialize: function InitDarkroomMirrorPlugin() {
            var buttonGroup = this.darkroom.toolbar.createButtonGroup();

            var mirrorXButton = buttonGroup.createButton({
                image: 'mirrorX'
            });
            var mirrorYButton = buttonGroup.createButton({
                image: 'mirrorY'
            });

            mirrorXButton.addEventListener('click', this.mirrorXImg.bind(this));
            mirrorYButton.addEventListener('click', this.mirrorYImg.bind(this));
        },

        mirrorXImg: function() {
            this.mirrorImg('X');
        },
        mirrorYImg: function() {
            this.mirrorImg('Y');
        },

        mirrorImg: function(XorY) {
            this.darkroom.applyTransformation(
                new Mirror({XorY: XorY})
            );
        },

    });

})();
