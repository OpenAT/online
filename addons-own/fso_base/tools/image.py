# -*- coding: utf-8 -*-
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from PIL import Image


def resize_to_thumbnail(img, box=(440, 440), fit='mid'):
    """Downsample the image.
    @param img: Image - base64 Image Data
    @param box: tuple(x, y) - the bounding box of the result image
    @param fit: char - 'top' crops to the top, any other value crops to the middle
    """

    # DECODE the img to an base64 PIL object
    img = Image.open(StringIO.StringIO(img.decode('base64')))
    filetype = img.format.upper()
    filetype = {'BMP': 'PNG', }.get(filetype, filetype)
    if img.mode not in ["1", "L", "P", "RGB", "RGBA"]:
        img = img.convert("RGB")

    # Crop the image
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = 1.0 * x2/box[0]
        hRatio = 1.0 * y2/box[1]
        if hRatio > wRatio:
            y1 = int(y2/2-box[1]*wRatio/2)
            y2 = int(y2/2+box[1]*wRatio/2)
        else:
            x1 = int(x2/2-box[0]*hRatio/2)
            x2 = int(x2/2+box[0]*hRatio/2)
        if fit == 'top':
            y2 -= y1
            y1 = 0
        img = img.crop((x1, y1, x2, y2))

    # Resize the image
    img.thumbnail(box, Image.ANTIALIAS)

    # RETURN the image
    background_stream = StringIO.StringIO()
    img.save(background_stream, filetype)
    return background_stream.getvalue().encode('base64')
