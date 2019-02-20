(function () {
'use strict';

    var Resize = Darkroom.Transformation.extend({
        applyTransformation: function (canvas, image, next) {
            image.centeredScaling = true;
            image.lockScalingX = false;
            image.lockScalingY = false;

            // Different scaling options (scaling locked: width and height scale the same factor,
            // scaling unlocked: width and height scale with different factor)
            if (this.options.scale) {
                image.scale(this.options.scale);
            } else if (this.options.scaleY) {
                image.scaleY = this.options.scaleY;
            } else if (this.options.scaleX) {
                image.scaleX = this.options.scaleX;
            }

            // Refresh of the canvas to show the changes
            if (this.options.triggerNext === undefined) {
                this.options.darkroom.refresh();
            }

            if (this.options.triggerNext) {
                // apply the resizing of the image
                var resizeFilter = new fabric.Image.filters.Resize(image, {
                    scaleX: this.options.scaleX,
                    scaleY: this.options.scaleY
                });
                image.filters.push(resizeFilter);
                image.applyFilters();

                next();
            }
        },
    });

    Darkroom.plugins['resize'] = Darkroom.Plugin.extend({
        initialize: function InitDarkroomRotatePlugin () {
            var buttonGroup = this.darkroom.toolbar.createButtonGroup();

            this.resizeButton = buttonGroup.createButton({
              image: 'resize'
            });
            this.okButton = buttonGroup.createButton({
                image: 'done',
                type: 'success',
                hide: true
            });
            this.cancelButton = buttonGroup.createButton({
                image: 'close',
                type: 'danger',
                hide: true
            });

            this.resizeButton.addEventListener('click', this.toggleActivity.bind(this));
            this.okButton.addEventListener('click', this.resizeImage.bind(this));
            this.cancelButton.addEventListener('click', this.setInactive.bind(this));

            this.resizeSwitch = document.getElementById('resize_Switch_checkbox');
            this.lockResizeBar();
            this.resizeSwitch.addEventListener('click', this.toggleLock.bind(this));

            this.resizeSliderWidth = document.getElementById('sliderbar_Width');
            this.resizeSliderWidth.addEventListener('input', this.resizeImageW.bind(this));

            this.resizeSliderHeight = document.getElementById('sliderbar_Height');
            this.resizeSliderHeight.addEventListener('input', this.resizeImageH.bind(this));
        },

        toggleActivity: function () {
            if (!this.checkActive()) {
                this.setActive();
            } else
                this.setInactive();
        },

        checkActive: function () {
            return this.activeResize !== undefined;
        },

        setActive: function () {
            this.activeResize = true;
            this.resizeButton.active(true);
            this.okButton.hide(false);
            this.cancelButton.hide(false);
            this.darkroom.resizeActive(true);
        },

        setInactive: function () {
            this.activeResize = undefined;
            this.resizeButton.active(false);
            this.okButton.hide(true);
            this.cancelButton.hide(true);
            this.darkroom.resizeActive(false);
        },

        resizeImage: function () {
            if (this.resizeSwitch.checked === true) {
                this.darkroom.applyTransformation(
                    new Resize({scaleX: this.resizeSliderWidth.value / 100,
                                scaleY: this.resizeSliderHeight.value / 100,
                                triggerNext: true})
                );
            } else {
                this.darkroom.applyTransformation(
                    new Resize({scaleX: this.resizeSliderWidth.value / 100,
                                scaleY: this.resizeSliderWidth.value / 100,
                                triggerNext: true})
                );
            }
            this.resizeSwitch.checked = false;
            this.lockResizeBar();
            this.resizeSliderWidth.value = 100;
            this.resizeSliderHeight.value = 100;
        },

        resizeImageW: function () {
            if (this.resizeSwitch.checked === true) {
                this.darkroom.applyTransformation(
                    new Resize({scaleX: this.resizeSliderWidth.value / 100,
                                darkroom: this.darkroom})
                );
            } else {
                this.darkroom.applyTransformation(
                    new Resize({scale: this.resizeSliderWidth.value / 100,
                                darkroom: this.darkroom})
                );
            }
        },

        resizeImageH: function () {
            this.darkroom.applyTransformation(
                new Resize({scaleY: this.resizeSliderHeight.value / 100,
                            darkroom: this.darkroom})
            );

        },

        toggleLock: function () {
            if (this.resizeSwitch.checked === true) {
                this.unlockResizeBar();
            } else {
                this.lockResizeBar();
            }
        },

        lockResizeBar: function () {
            $('.sliderHeight').addClass('disabled');
        },

        unlockResizeBar: function () {
            $('.sliderHeight').removeClass('disabled');
        },
    });
})();
