(function() {
'use strict';

    var Circle = Darkroom.Transformation.extend({
        applyTransformation: function(canvas, image, next) {
            image.scale(1).set({
                clipTo: this.roundImg.bind(image)
            });
            canvas.add(image).setActiveObject(image);
            canvas.renderAll();

            next();
        },
        roundImg: function(ctx) {
            var ellip = new fabric.Ellipse({
                left: 0,
                top: 0,
                originX: 'center',
                originY: 'center',
                rx: this.width / 2,
                ry: this.height / 2
          });
          ctx.fillStyle = 'transparent';
          ellip._render(ctx, false);
        }

    });

    Darkroom.plugins['circle'] = Darkroom.Plugin.extend({

        initialize: function InitDarkroomMirrorPlugin() {
            var buttonGroup = this.darkroom.toolbar.createButtonGroup();

            var circleButton = buttonGroup.createButton({
                image: 'circle'
            });

            circleButton.addEventListener('click', this.circleImg.bind(this));
        },

        circleImg: function() {
            this.darkroom.applyTransformation(
                new Circle()
            );
        },

    });

})();
