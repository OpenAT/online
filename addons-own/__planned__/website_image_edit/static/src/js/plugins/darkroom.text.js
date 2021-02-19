(function() {
'use strict';

    var Text = Darkroom.Transformation.extend({
        applyTransformation: function(canvas, image, next) {
//            console.log('addText');
//            console.log(canvas);
//            console.log(canvas.width);
//            console.log(canvas.height);
//            console.log(image.width / 2);
//            console.log(image.height / 2);

            canvas.add(new fabric.IText('Text Eingeben', {
                  left: image.width / 2,
                  top: image.height / 2,
                  fontFamily: 'arial black',
                  fill: '#333',
                  fontSize: 50
            }));
            canvas.renderAll();
        }

    });

    Darkroom.plugins['text'] = Darkroom.Plugin.extend({

        initialize: function InitDarkroomMirrorPlugin() {
            var buttonGroup = this.darkroom.toolbar.createButtonGroup();

            var textButton = buttonGroup.createButton({
                image: 'text'
            });

            textButton.addEventListener('click', this.addText.bind(this));
        },

        addText: function() {
            this.darkroom.applyTransformation(
                new Text()
            );
        },

    });

})();
