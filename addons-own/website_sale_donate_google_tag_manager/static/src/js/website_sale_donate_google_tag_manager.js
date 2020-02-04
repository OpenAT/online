// BEST TUTORIAL: https://www.simoahava.com/analytics/enhanced-ecommerce-guide-for-google-tag-manager
$(document).ready(function () {

    function get_odoo_product_details_for_gtm (odoo_product_html) {
        if (! odoo_product_html || ! odoo_product_html.length) {
            console.log('odoo_product_html is empty!');
            return {}
        }

        var $odoo_product = odoo_product_html;
        if (! $odoo_product instanceof jQuery) {
            console.log('odoo_product_html is no jquery object!');
            $odoo_product = $(odoo_product_html)
        }

        var gtm_product_data = {
            'name': $odoo_product.find("[itemprop=name]").text(),         // Name or ID is required.
            'id': $odoo_product.find("input[name=product_id]").val(),
            'price': $odoo_product.find("input[name=price_donate]").val() || $odoo_product.find("[itemprop=price]").text(),
            'category': $odoo_product.find("input[name=cat_id]").val()
        };
        return gtm_product_data;
    }

    // PRODUCT IMPRESSIONS: PRODUCT LISTING PAGE (LIST OF PRODUCTS)
    // https://developers.google.com/tag-manager/enhanced-ecommerce#product-impressions
    // --------------------------------------------------------------------------------
    // Find all products on the page
    var gtm_product_impressions = [];
    var $odoo_products = $("#products_grid .oe_product");
    if ($odoo_products.length) {
        // Loop through all odoo products on shop product listing pages
        // https://stackoverflow.com/questions/10179815/get-loop-counter-index-using-for-of-syntax-in-javascript
        $odoo_products.each(function (i) {
            var odoo_product_detail = get_odoo_product_details_for_gtm($(this));
            odoo_product_detail['position'] = i+1;
            gtm_product_impressions.push(odoo_product_detail)
        });
    }
    // Add the collected product data to the Google Tag Manager dataLayer object
    if (gtm_product_impressions.length) {
        console.log('Push GTM Data Layer Event "fsonline.product_listing"', gtm_product_impressions);
        dataLayer.push({
            'event': 'fsonline.product_listing',
            'ecommerce': {
                'impressions': gtm_product_impressions
            }
        });
    }

    // PRODUCT IMPRESSIONS: PRODUCT DETAIL (PRODUCT PAGE)
    // https://developers.google.com/tag-manager/enhanced-ecommerce#details
    var $odoo_product_page = $("#product_detail.oe_website_sale");
    if ($odoo_product_page.length) {
        var odoo_product_detail = get_odoo_product_details_for_gtm($odoo_product_page);
        // Measure a view of product details. This example assumes the detail view occurs on pageload,
        // and also tracks a standard pageview of the details page.
        console.log('Push GTM Data Layer Event "fsonline.product_detail"', odoo_product_detail);
        dataLayer.push({
            'event': 'fsonline.product_detail',
            'ecommerce': {
                'detail': {
                    //'actionField': {'list': 'Apparel Gallery'},    // 'detail' actions have an optional list property.
                    'products': [odoo_product_detail]
                }
            }
        });
    }

    // ADD TO CART
    $(".oe_website_sale form[action='/shop/cart/update']").submit( function() {
        var odoo_product_detail = get_odoo_product_details_for_gtm($("#product_detail.oe_website_sale"));
        odoo_product_detail['quantity'] = $(this).find("input[name=add_qty]").val();
        console.log('Push GTM Data Layer Event "fsonline.addToCart"', odoo_product_detail);
        // Measure adding a product to a shopping cart by using an 'add' actionFieldObject
        // and a list of productFieldObjects.
        dataLayer.push({
          'event': 'fsonline.addToCart',
          'ecommerce': {
            'add': {                                // 'add' actionFieldObject measures.
              'products': [odoo_product_detail]
            }
          }
        });
    });

    // TODO: REMOVE FROM CART (send remaining number of product items in the cart!)
    // Measure adding a product to a shopping cart by using an 'add' actionFieldObject
    // and a list of productFieldObjects.

    // CHECKOUT STEP 1: USER DATA
    // TODO: CHECKOUT STEP 1 OPTION: SELECT SHIPPING METHOD (Will not be done right now because rarely used!)
    // HINT: The products array should only be sent with the first step. Sending it with any other step will do nothing.
    // Step 1: Data of the Buyer
    if ($("#wsd_checkout_form").length) {
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                console.log('Push GTM Data Layer Event "fsonline.checkout" step 1 user data', gtm_sale_order_data);
                dataLayer.push({
                    'event': 'fsonline.checkout',
                    'ecommerce': {
                        'currencyCode': gtm_sale_order_data.currencyCode,
                        'checkout': {
                            'actionField': {'step': 1},
                            'products': gtm_sale_order_data.products
                        }
                    },
                });
            }
        });
    }

    // CHECKOUT STEP 2: PAYMENT
    // CHECKOUT STEP 2 CHECKOUT OPTION: SELECTED PAYMENT METHOD
    if ($("#payment_method").length) {
        var active_acquirer = $('#payment_method li.active input[name=acquirer]').val() + '__' + $('#payment_method li.active .tab-acquirer-name').text();
        console.log('Push GTM Data Layer Event "fsonline.checkout" step 2 payment', active_acquirer);
        dataLayer.push({
            'event': 'fsonline.checkout',
            'ecommerce': {
                'checkout': {
                    'actionField': {
                        'step': 2,
                        'option': active_acquirer
                    },
                }
            },
        });
    }
    // Track payment method changes
    $('#payment_method a[role="tab"]').on("click", function () {
        var selected_acquirer = $(this).find('input[name=acquirer]').val() + '__' + $(this).find('.tab-acquirer-name').text();
        console.log('Push GTM Data Layer Event "fsonline.checkout_option" step 2 payment > selected payment method', selected_acquirer);
        dataLayer.push({
            'event': 'fsonline.checkout_option',
            'ecommerce': {
                'checkout_option': {
                    'actionField': {
                        'step': 2,
                        'option': selected_acquirer
                    },
                }
            },
        });
    });

    // PURCHASE (This is the final redirect to the payment provider)
    $(".js_auto_submit_form form").submit( function () {
        console.log('.js_auto_submit_form = final redirect to the payment provider!');
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                console.log('Push GTM Data Layer Event "fsonline.purchase"', gtm_sale_order_data);
                dataLayer.push({
                    event: 'fsonline.purchase',
                    'ecommerce': {
                        'purchase': {
                            'actionField': gtm_sale_order_data.order_data,
                            'products': gtm_sale_order_data.products
                        }
                    }
                });
            }
        });
    });
    $("form.payment_opc_acquirer_form").submit( function () {
        console.log('form.payment_opc_acquirer_form submission!');
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                console.log('Push GTM Data Layer Event "fsonline.purchase"', gtm_sale_order_data);
                dataLayer.push({
                    event: 'fsonline.purchase',
                    'ecommerce': {
                        'purchase': {
                            'actionField': gtm_sale_order_data.order_data,
                            'products': gtm_sale_order_data.products
                        }
                    }
                });
            }
        });
    });

});
