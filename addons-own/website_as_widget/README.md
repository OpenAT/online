# website_as_widget

Call webpages as widgets (without header or footer).

## ENABLE aswidget Version
```http://dadi.datadialog.net/shop?aswidget=True```

## DISABLE aswidget Version
```http://dadi.datadialog.net/shop?aswidget=False```

## Example
Example of a page hosting an I-Frame (= Organisations Webpage) 
that shows the page ```dadi.datadialog.net/shop``` inside the I-Frame:
```html
<head>
    <title>I-Frame-Embedding Example Page </title>

    <script type="text/javascript">
        //MDN PolyFil for IE8 (This is not needed if you use the jQuery version)
        if (!Array.prototype.forEach){
            Array.prototype.forEach = function(fun /*, thisArg */){
            "use strict";
            if (this === void 0 || this === null || typeof fun !== "function") throw new TypeError();

            var
            t = Object(this),
            len = t.length >>> 0,
            thisArg = arguments.length >= 2 ? arguments[1] : void 0;

            for (var i = 0; i < len; i++)
            if (i in t)
                fun.call(thisArg, t[i], i, t);
            };
        }
    </script>
    
    <script type="text/javascript" 
            src="http://dadi.datadialog.net/website_tools/static/lib/iframe-resizer/js/iframeResizer.min.js"/>

</head>

<body>
<h1>Above I-Frame</h1>
<p>Some content above the iframe</p>

<iframe class="fso_iframe" src="http://dadi.datadialog.net/shop?aswidget=True"
        scrolling="no" frameborder="0" width="100%"
        style="width:100%; border:none; padding:0; margin:0;">
</iframe>
<script type="text/javascript">
    iFrameResize({
        log: false,
        enablePublicMethods: true,
        checkOrigin: false,
        inPageLinks: true,
        heightCalculationMethod: taggedElement,
    }, '.fso_iframe')
</script>


<h1>Below I-Frame</h1>
<p>Some content below the iframe</p>
</body>
```

## Documentation and Credits
- https://github.com/davidjbradshaw/iframe-resizer

