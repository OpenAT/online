$(document).ready(function () {

    // Product Impressions: Product Listing Page (Multiple products on one page)
    // https://developers.google.com/tag-manager/enhanced-ecommerce#product-impressions
    if ($("#products_grid .oe_product.oe_grid").length) {
        dataLayer.push({
          'ecommerce': {
            'currencyCode': 'EUR',                       // Local currency is optional.
            'impressions': [
             {
               'name': 'Triblend Android T-Shirt',       // Name or ID is required.
               'id': '12345',
               'price': '15.25',
               'brand': 'Google',
               'category': 'Apparel',
               'variant': 'Gray',
               'list': 'Search Results',
               'position': 1
             },
             {
               'name': 'Donut Friday Scented T-Shirt',
               'id': '67890',
               'price': '33.75',
               'brand': 'Google',
               'category': 'Apparel',
               'variant': 'Black',
               'list': 'Search Results',
               'position': 2
             }]
          }
        });
    }

    // Product Impressions: Product Detail (The product detail page)
    // https://developers.google.com/tag-manager/enhanced-ecommerce#details
    if ($("#product_detail.oe_website_sale").length) {
        // Measure a view of product details. This example assumes the detail view occurs on pageload,
        // and also tracks a standard pageview of the details page.
        dataLayer.push({
          'ecommerce': {
            'detail': {
              'actionField': {'list': 'Apparel Gallery'},    // 'detail' actions have an optional list property.
              'products': [{
                'name': 'Triblend Android T-Shirt',         // Name or ID is required.
                'id': '12345',
                'price': '15.25',
                'brand': 'Google',
                'category': 'Apparel',
                'variant': 'Gray'
               }]
             }
           }
        });
    }

    // Product Clicks (Maybe this is not needed?!? Or only on shop listing pages)
    // https://developers.google.com/tag-manager/enhanced-ecommerce#product-clicks
    /**
     * Call this function when a user clicks on a product link. This function uses the event
     * callback datalayer variable to handle navigation after the ecommerce data has been sent
     * to Google Analytics.
     * @param {Object} productObj An object representing a product.
     */
    function(productObj) {
      dataLayer.push({
        'event': 'productClick',
        'ecommerce': {
          'click': {
            'actionField': {'list': 'Search Results'},      // Optional list property.
            'products': [{
              'name': productObj.name,                      // Name or ID is required.
              'id': productObj.id,
              'price': productObj.price,
              'brand': productObj.brand,
              'category': productObj.cat,
              'variant': productObj.variant,
              'position': productObj.position
             }]
           }
         },
         'eventCallback': function() {
           document.location = productObj.url
         }
      });
    }


    // FOR REFERENCE AND TO REMOVE  ===================================================================================
    // Watching a product
    if ($("#product_detail.oe_website_sale").length) {
        prod_id = $("input[name='product_id']").attr('value');
        vpv("/stats/ecom/product_view/" + prod_id);
    }

    // Add a product into the cart
    $(".oe_website_sale form[action='/shop/cart/update'] a.a-submit").on('click', function(o) {
        prod_id = $("input[name='product_id']").attr('value');
        vpv("/stats/ecom/product_add_to_cart/" + prod_id);
    });

    // Start checkout
    $(".oe_website_sale a[href='/shop/checkout']").on('click', function(o) {
        vpv("/stats/ecom/customer_checkout");
    });

    $(".oe_website_sale div.oe_cart a[href^='/web?redirect'][href$='/shop/checkout']").on('click', function(o) {
        vpv("/stats/ecom/customer_signin");
    });

    $(".oe_website_sale form[action='/shop/confirm_order'] a.a-submit").on('click', function(o) {
        if ($("#top_menu > li > a[href='/web/login']").length){
            vpv("/stats/ecom/customer_signup");
        }
        vpv("/stats/ecom/order_checkout");
    });

    $(".oe_website_sale form[target='_self'] button[type=submit]").on('click', function(o) {
        var method = $("#payment_method input[name=acquirer]:checked").nextAll("span:first").text();
        vpv("/stats/ecom/order_payment/" + method);
    });

    if ($(".oe_website_sale div.oe_cart div.oe_website_sale_tx_status").length) {
        track_ga('require', 'ecommerce');

        order_id = $(".oe_website_sale div.oe_cart div.oe_website_sale_tx_status").data("order-id");
        vpv("/stats/ecom/order_confirmed/" + order_id);

        openerp.jsonRpc("/shop/tracking_last_order/").then(function(o) {
            track_ga('ecommerce:clear');

            if (o.transaction && o.lines) {
                track_ga('ecommerce:addTransaction', o.transaction);
                _.forEach(o.lines, function(line) {
                    track_ga('ecommerce:addItem', line);
                });
            }
            track_ga('ecommerce:send');
        });
    }

    function vpv(page){ //virtual page view
        track_ga('send', 'pageview', {
          'page': page,
          'title': document.title,
        });
    }

    function track_ga() {
        website_ga = this.ga || function(){};
        website_ga.apply(this, arguments);
    }

});
