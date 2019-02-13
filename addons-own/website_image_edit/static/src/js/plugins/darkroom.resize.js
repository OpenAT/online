(function() {
'use strict';

    var Resize = Darkroom.Transformation.extend({
        applyTransformation: function(canvas, image, next) {
            console.log('resize');
            console.log(this.options.scale);

            image.filters.push(new fabric.Image.filters.Resize(
            {
                resizeType: 'sliceHack',
                scaleX: this.options.scale,
                scaleY: this.options.scale,
            }
            ));
            image.applyFilters(canvas.renderAll.bind(canvas));

            canvas.renderAll();
            next();
        }
    });

    var ResizeScroll = Darkroom.Transformation.extend({
        imageRatio: function createImageRatioSize(maxW, maxH, imgW, imgH) {
            var ratio = imgH / imgW;
            if (imgW >= maxW && ratio <= 1){
                imgW = maxW;
                imgH = imgW * ratio;
            } else if(imgH >= maxH){
                imgH = maxH;
                imgW = imgH / ratio;
            } else if (ratio !== 1) {
                if (imgW > imgH) {
                    imgW = maxW;
                    imgH = imgW * ratio;
                } else {
                    imgH = maxH;
                    imgW = imgH / ratio;
                }
            }

            return {
                w: imgW,
                h: imgH
            };
        },

        applyTransformation: function(canvas, image, next) {
            console.log('resize scroll');

            var containerW = canvas.width;
            var containerH = canvas.height;
            var leftStart = containerW;
//            var canvas2 = new fabric.Canvas('zoom', {
//                width: containerW,
//                height: 500
//            });
            var maxW = containerW;
            var maxH = containerH;
            console.log(image._element)

            var $img = $('.main-img > img');
            var imgElement = image._element;
            var origH = image.height;
            var origW = image.width;
            var imageSize = imageRatio(maxW, maxH, origW, origH);
            var imgW = imageSize.w;
            var imgH = imageSize.h;
            var initScaleH = imgH / origH;
            var initScaleW = imgW / origW;
            var originalZoomHandlerCenter;

            var sliderBar = new fabric.Rect({
                fill: 'rgb(90, 222, 90)',
                opacity: 0.7,
                height: 4,
                width: 294,
                top: maxH - 50 + 3,
                left: (leftStart / 2) - 150 + 3,
                hasControls: false,
                hasBorders: false,
                hoverCursor: 'cursor',
                lockMovementY: true,
                lockMovementX: true
            });

            var zoomHandlerTop = sliderBar.top - (15 - (sliderBar.height / 2));
            var zoomHandler = new fabric.Circle({
                fill: 'rgb(150, 222, 150)',
                opacity: 0.7,
                radius: 15,
                top: zoomHandlerTop,
                left: (leftStart / 2) - (sliderBar.width / 2) + 15,
                hasControls: false,
                hasBorders: false,
                lockMovementY: true,
                hoverCursor: 'pointer'
            });

            var imgInstance = new fabric.Image(imgElement, {
                left: (leftStart / 2) - (imgW / 2),
                top: 0,
                hasControls: false,
                centeredScaling: true,
                lockUniScaling: true,
                lockRotation: true,
                hasBorders: false,
                hoverCursor: 'cursor',
                lockMovementY: true,
                lockMovementX: true
            });

            var incrementer = sliderBar.width / 100;

            zoomHandler.on('moving', function (e) {
                var top = zoomHandler.top;
                var bottom = top + zoomHandler.height;
                var left = zoomHandler.left;
                var right = left + zoomHandler.width;

                var topBound = sliderBar.top;
                var bottomBound = topBound + sliderBar.height;
                var leftBound = sliderBar.left;
                var rightBound = leftBound + sliderBar.width;
                var zoomHandlerCenterX = zoomHandler.width / 2;

                var xBounds = Math.min(Math.max(left, leftBound - zoomHandlerCenterX), rightBound - zoomHandlerCenterX);
                var yBounds = Math.min(Math.max(top, topBound), bottomBound - ((zoomHandler.height / 2) + (sliderBar.height / 2)));

                // capping logic here
                zoomHandler.setLeft(xBounds);
                zoomHandler.setTop(yBounds);

            });
//
//            canvas.on("mouse:up", function(e) {
//                var left = zoomHandler.left;
//                var leftBound = sliderBar.left;
//                var rightBound = leftBound + sliderBar.width;
//                var zoomHandlerCenterX = zoomHandler.width / 2;
//
//                var xBounds = Math.min(Math.max(left, leftBound - zoomHandlerCenterX), rightBound - zoomHandlerCenterX);
//
//                if (left >= xBounds && left <= xBounds && (e.target && !e.target._element)) {
//                    if (imgInstance.width) {
//                        var newLeft = left / 100;
//                        var newScale = newLeft / incrementer;
//                        imgInstance.animate('scaleY', newScale, {
//                            onChange: canvas.renderAll.bind(canvas),
//                            easing: fabric.util.ease.easeOutQuad
//                        });
//                        canvas.renderAll();
//                        imgInstance.animate('scaleX', newScale, {
//                            onChange: canvas.renderAll.bind(canvas),
//                            easing: fabric.util.ease.easeOutQuad
//                        });
//                    }
//                }
//            });

            canvas.renderAll();
            next();
        },


    });

    Darkroom.plugins['resize'] = Darkroom.Plugin.extend({

        initialize: function InitDarkroomRotatePlugin() {
            var buttonGroup = this.darkroom.toolbar.createButtonGroup();

            var resizeButton = buttonGroup.createButton({
              image: 'resize'
            });

            var compressButton = buttonGroup.createButton({
              image: 'compress'
            });
            var expandButton = buttonGroup.createButton({
              image: 'expand'
            });

            resizeButton.addEventListener('click', this.resize.bind(this));
            compressButton.addEventListener('click', this.compress.bind(this));
            expandButton.addEventListener('click', this.expand.bind(this));
        },

        compress: function compress () {
            this.darkroom.applyTransformation(
                new Resize({scale: 0.9})
            );
        },
        expand: function expand () {
            this.darkroom.applyTransformation(
                new Resize({scale: 1.1})
            );
        },

        resize: function resize() {
            this.darkroom.applyTransformation(
                new ResizeScroll()
            );
        }


    });

})();



//var $canvasContainer = $('.canvas-wrapper');
//var containerW = $canvasContainer.width();
//var containerH = $canvasContainer.height();
//var leftStart = containerW;
//var canvas = new fabric.Canvas('zoom', {
//    width: containerW,
//    height: 500
//});
//var maxW = containerW;
//var maxH = containerH;
//
//var $img = $('.main-img > img');
//var imgElement = $img[0];
//var origH = $img.height();
//var origW = $img.width();
//var imageSize = imageRatio(maxW, maxH, origW, origH);
//var imgW = imageSize.w;
//var imgH = imageSize.h;
//var initScaleH = imgH / origH;
//var initScaleW = imgW / origW;
//var originalZoomHandlerCenter;
//
//var sliderBar = new fabric.Rect({
//    fill: 'rgb(90, 222, 90)',
//    opacity: 0.7,
//    height: 4,
//    width: 294,
//    top: maxH - 50 + 3,
//    left: (leftStart / 2) - 150 + 3,
//    hasControls: false,
//    hasBorders: false,
//    hoverCursor: 'cursor',
//    lockMovementY: true,
//    lockMovementX: true
//});
//
//var zoomHandlerTop = sliderBar.top - (15 - (sliderBar.height / 2));
//var zoomHandler = new fabric.Circle({
//    fill: 'rgb(150, 222, 150)',
//    opacity: 0.7,
//    radius: 15,
//    top: zoomHandlerTop,
//    left: (leftStart / 2) - (sliderBar.width / 2) + 15,
//    hasControls: false,
//    hasBorders: false,
//    lockMovementY: true,
//    hoverCursor: 'pointer'
//});
//
//var imgInstance = new fabric.Image(imgElement, {
//    left: (leftStart / 2) - (imgW / 2),
//    top: 0,
//    hasControls: false,
//    centeredScaling: true,
//    lockUniScaling: true,
//    lockRotation: true,
//    hasBorders: false,
//    hoverCursor: 'cursor',
//    lockMovementY: true,
//    lockMovementX: true
//});
//
//var incrementer = sliderBar.width / 100;
//
//zoomHandler.on('moving', function (e) {
//    var top = zoomHandler.top;
//    var bottom = top + zoomHandler.height;
//    var left = zoomHandler.left;
//    var right = left + zoomHandler.width;
//
//    var topBound = sliderBar.top;
//    var bottomBound = topBound + sliderBar.height;
//    var leftBound = sliderBar.left;
//    var rightBound = leftBound + sliderBar.width;
//    var zoomHandlerCenterX = zoomHandler.width / 2;
//
//    var xBounds = Math.min(Math.max(left, leftBound - zoomHandlerCenterX), rightBound - zoomHandlerCenterX);
//    var yBounds = Math.min(Math.max(top, topBound), bottomBound - ((zoomHandler.height / 2) + (sliderBar.height / 2)));
//
//    // capping logic here
//    zoomHandler.setLeft(xBounds);
//    zoomHandler.setTop(yBounds);
//
//});
//
//canvas.on("mouse:up", function(e) {
//    var left = zoomHandler.left;
//    var leftBound = sliderBar.left;
//    var rightBound = leftBound + sliderBar.width;
//    var zoomHandlerCenterX = zoomHandler.width / 2;
//
//    var xBounds = Math.min(Math.max(left, leftBound - zoomHandlerCenterX), rightBound - zoomHandlerCenterX);
//
//    if (left >= xBounds && left <= xBounds && (e.target && !e.target._element)) {
//        if (imgInstance.width) {
//            var newLeft = left / 100;
//            var newScale = newLeft / incrementer;
//            imgInstance.animate('scaleY', newScale, {
//                onChange: canvas.renderAll.bind(canvas),
//                easing: fabric.util.ease.easeOutQuad
//            });
//            canvas.renderAll();
//            imgInstance.animate('scaleX', newScale, {
//                onChange: canvas.renderAll.bind(canvas),
//                easing: fabric.util.ease.easeOutQuad
//            });
//        }
//    }
//});
//
//var stuff = {
//    init: function () {
//        imgInstance.set({
//            scaleY: imgH / origH,
//            scaleX: imgW / origW
//        });
//        canvas.add(imgInstance, sliderBar, zoomHandler);
//        canvas.bringToFront(sliderBar);
//        canvas.bringToFront(zoomHandler);
//        originalZoomHandlerCenter = zoomHandler.getCenterPoint();
//
//    }
//};
//
//$(function () {
//    stuff.init();
//});
