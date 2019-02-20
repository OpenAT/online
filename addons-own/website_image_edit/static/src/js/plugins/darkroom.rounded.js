(function() {
'use strict';

    var roundedCorner = Darkroom.Transformation.extend({
        applyTransformation: function(canvas, image, next) {
            image.scale(1).set({
                clipTo: this.roundedCorners.bind(image)
            });
            canvas.add(image).setActiveObject(image);
            canvas.renderAll();

            next();
        },
        roundedCorners: function(ctx) {
            var rect = new fabric.Rect({
                left: 0,
                top: 0,
                rx: 20 / this.scaleX,
                ry: 20 / this.scaleY,
                width: this.width,
                height: this.height,
          });
          ctx.fillStyle = 'transparent';
          rect._render(ctx, false);
        }
    });

    Darkroom.plugins['rounded'] = Darkroom.Plugin.extend({

        initialize: function InitDarkroomMirrorPlugin() {
            var buttonGroup = this.darkroom.toolbar.createButtonGroup();

            var roundedButton = buttonGroup.createButton({
                image: 'rounded'
            });

            roundedButton.addEventListener('click', this.roundedImg.bind(this));
        },

        roundedImg: function() {
            this.darkroom.applyTransformation(
                new roundedCorner()
            );
        },

    });

})();
