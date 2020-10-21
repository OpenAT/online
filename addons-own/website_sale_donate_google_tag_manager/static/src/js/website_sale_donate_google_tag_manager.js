// BEST TUTORIAL: https://www.simoahava.com/analytics/enhanced-ecommerce-guide-for-google-tag-manager

// HELPER FUNCTION TO READ PRODUCT DETAILS FROM PAGE HTML
function get_odoo_product_details_for_gtm (odoo_product_html) {
    if (! odoo_product_html || ! odoo_product_html.length) {
        console.log('odoo_product_html is empty!');
        return {}
    }

    let $odoo_product = odoo_product_html;
    if (! $odoo_product instanceof jQuery) {
        console.log('odoo_product_html is no jquery object!');
        $odoo_product = $(odoo_product_html)
    }

    return {
        'name': $odoo_product.find("[itemprop=name]").text(),                         // Name or ID is required.
        'id': $odoo_product.find("div.js_product").data('product-template-id'),       // the product-template-id
        'price': $odoo_product.find("input[name=price_donate]").val() || $odoo_product.find("[itemprop=price]").text(),
        'category': $odoo_product.find("input[name=cat_id]").val(),
        'variant': $odoo_product.find("input[name=product_id]").val(),  // the selected product-variant-id
    };
}

// Google Tag Manager Events
$(document).ready(function () {
    // --------------------------------------------------------------------------------
    // PRODUCT DETAIL (PRODUCT PAGE)
    // https://developers.google.com/tag-manager/enhanced-ecommerce#details
    // --------------------------------------------------------------------------------
    var $odoo_product_page = $("#product_detail");
    if ($odoo_product_page.length) {
        var odoo_product_detail = get_odoo_product_details_for_gtm($odoo_product_page);
        // Measure a view of product details. This example assumes the detail view occurs on pageload,
        // and also tracks a standard pageview of the details page.
        let event_data = {
            'event': 'fsonline.product_detail',
            'ecommerce': {
                'detail': {
                    //'actionField': {'list': 'Apparel Gallery'},    // 'detail' actions have an optional list property.
                    'products': [odoo_product_detail]
                }
            }
        };
        console.log(`Push GTM Data Layer Event "fsonline.product_detail":\n${JSON.stringify(event_data, undefined, 2)}`);
        dataLayer.push(event_data);
    }

    // --------------------------------------------------------------------------------
    // PRODUCT IMPRESSIONS (LIST OF PRODUCTS PAGE)
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
        let event_data = {
            'event': 'fsonline.product_listing',
            'ecommerce': {
                'impressions': gtm_product_impressions
            }
        };
        console.log(`Push GTM Data Layer Event "fsonline.product_listing":\n${JSON.stringify(event_data, undefined, 2)}`);
        dataLayer.push(event_data);
    }

    // --------------------------------------------------------------------------------
    // ADD TO CART / REMOVE FROM CART
    // --------------------------------------------------------------------------------
    $(".oe_website_sale form[action='/shop/cart/update']").submit( function() {
        var odoo_product_detail = get_odoo_product_details_for_gtm($("#product_detail.oe_website_sale"));
        var quantity = $(this).find("input[name=add_qty]").val();
        odoo_product_detail['quantity'] = quantity;

        // Measure adding a product to a shopping cart by using an 'add' actionFieldObject
        // and a list of productFieldObjects.
        if (quantity > 0) {
            let event_data = {
                'event': 'fsonline.addToCart',
                'ecommerce': {
                    'add': {
                        'products': [odoo_product_detail]
                    }
                }
            };
            console.log(`Push GTM Data Layer Event "fsonline.addToCart":\n${JSON.stringify(event_data, undefined, 2)}`);
            dataLayer.push(event_data);
        } else {
            let event_data = {
                'event': 'fsonline.removeFromCart',
                'ecommerce': {
                    'remove': {
                        'products': [odoo_product_detail]
                    }
                }
            };
            console.log(`Push GTM Data Layer Event "fsonline.removeFromCart":\n${JSON.stringify(event_data, undefined, 2)}`);
            dataLayer.push(event_data);
        }

    });

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 1: CART
    // https://developers.google.com/tag-manager/enhanced-ecommerce#checkoutstep
    // HINT: This step will be skipped more often than not by the shop settings
    // --------------------------------------------------------------------------------
    if ($("#wsd_cart_page").length) {
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                let event_data = {
                    'event': 'fsonline.checkout.cart',
                    'ecommerce': {
                        'currencyCode': gtm_sale_order_data.currencyCode,
                        'checkout': {
                            'actionField': {'step': 1},
                            'products': gtm_sale_order_data.products
                        }
                    },
                }
                console.log(`Push GTM Data Layer Event fsonline.checkout.cart:\n${JSON.stringify(event_data, undefined, 2)}`);
                dataLayer.push(event_data);
            }
        });
    }

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 2: USER DATA
    // https://developers.google.com/tag-manager/enhanced-ecommerce#checkoutstep
    // --------------------------------------------------------------------------------
    // TODO: CHECKOUT STEP 1 OPTION: SHIPPING METHOD (Will not be done right now because rarely used!)
    // HINT: The products array should only be sent with the first step. Sending it with any other step will do nothing.
    // Step 1: Data of the Buyer
    if ($("#wsd_checkout_form").length) {
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                let event_data = {
                    'event': 'fsonline.checkout.userdata',
                    'ecommerce': {
                        'currencyCode': gtm_sale_order_data.currencyCode,
                        'checkout': {
                            'actionField': {'step': 2},
                            'products': gtm_sale_order_data.products
                        }
                    },
                }
                console.log(`Push GTM Data Layer Event fsonline.checkout.userdata:\n${JSON.stringify(event_data, undefined, 2)}`);
                dataLayer.push(event_data);
            }
        });
    }

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 3: PAYMENT
    // CHECKOUT STEP 3 CHECKOUT OPTION: SELECTED PAYMENT METHOD
    // --------------------------------------------------------------------------------
    if ($("#payment_method").length) {
        let active_acquirer = $('#payment_method li.active input[name=acquirer]').val() + '__' + $('#payment_method li.active .tab-acquirer-name').text();
        let event_data = {
            'event': 'fsonline.checkout.paymentmethod',
            'ecommerce': {
                'checkout': {
                    'actionField': {
                        'step': 3,
                        'option': active_acquirer
                    },
                }
            },
        };
        console.log(`Push GTM Data Layer Event fsonline.checkout.paymentmethod:\n${JSON.stringify(event_data, undefined, 2)}`);
        dataLayer.push(event_data);
    }
    // TRACK PAYMENT METHOD CHANGES
    // ----------------------------
    $('#payment_method a[role="tab"]').on("click", function () {
        let selected_acquirer = $(this).find('input[name=acquirer]').val() + '__' + $(this).find('.tab-acquirer-name').text();
        let event_data = {
            'event': 'fsonline.checkout_option.paymentmethod',
            'ecommerce': {
                'checkout_option': {
                    'actionField': {
                        'step': 3,
                        'option': selected_acquirer
                    },
                }
            },
        };
        console.log(`Push GTM Data Layer Event fsonline.checkout_option.paymentmethod: CHANGED PAYMENT METHOD:\n${JSON.stringify(event_data, undefined, 2)}`);
        dataLayer.push(event_data);
    });

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 5: CONFIRMATION PAGE (Thank you page - AFTER! the purchase below)
    // HINT: Step 5 might be missing completely if a custom redirect url was configured!
    // --------------------------------------------------------------------------------
    // TODO: Append the sale order data if any and send purchase cancellation request if the state of the so is
    //       e.g. cancelled
    if ($("div.wsd_confirmation_page").length) {
        let event_data = {
            'event': 'fsonline.confirmation_page_after_purchase',
            'ecommerce': {
                'checkout': {
                    'actionField': {
                        'step': 5,
                    },
                }
            },
        };
        console.log(`Push GTM Data Layer Event fsonline.confirmation_page_after_purchase:\n${JSON.stringify(event_data, undefined, 2)}`);
        dataLayer.push(event_data);
    }

});

// ---------------------------------------------------------------------------------
// PURCHASE (This is the final redirect to the payment provider) WOULD BE STEP 4 ...
// ---------------------------------------------------------------------------------
function pushGTMPurchaseEventOnSubmit(message){
    console.log('pushGTMPurchaseEventOnSubmit:', message);
    openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
        if (gtm_sale_order_data && gtm_sale_order_data.products) {
            let event_data = {
                'event': 'fsonline.purchase',
                'ecommerce': {
                    'purchase': {
                        'actionField': gtm_sale_order_data.order_data,
                        'products': gtm_sale_order_data.products
                    }
                }
            }
            console.log(`Push GTM Data Layer Event fsonline.purchase for ${message}:\n${JSON.stringify(event_data, undefined, 2)}`);
            dataLayer.push(event_data);
        }
    });
}
$("#wsd_pp_auto_submit_form.js_auto_submit_form form").on('submit', function(){
   pushGTMPurchaseEventOnSubmit("#wsd_pp_auto_submit_form .js_auto_submit_form form");
});
