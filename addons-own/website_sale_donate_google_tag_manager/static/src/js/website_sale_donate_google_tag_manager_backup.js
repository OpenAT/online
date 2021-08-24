// BEST TUTORIAL: https://www.simoahava.com/analytics/enhanced-ecommerce-guide-for-google-tag-manager

// HELPER FUNCTION TO READ PRODUCT DETAILS FROM PAGE HTML
function get_odoo_product_details_for_gtm (odoo_product_html) {
    if (! odoo_product_html || ! odoo_product_html.length) {
        console.log('odoo_product_html is empty!');
        return {}
    }

    let $odoo_product = odoo_product_html;
    if (! $odoo_product instanceof jQuery) {
        console.log('odoo_product_html is no a jquery object!');
        $odoo_product = $(odoo_product_html)
    }

    // console.log(`odoo_product_html:\n${odoo_product_html.html()}`);

    return {
        'name': $odoo_product.find("[itemprop=name]").text(),                         // Name or ID is required.
        'id': $odoo_product.find("div.js_product").data('product-template-id'),       // the product-template-id
        'price': $odoo_product.find("input[name=price_donate]").val() || $odoo_product.find("[itemprop=price]").text(),
        'category': $odoo_product.find("input[name=cat_id]").val(),
        'variant': $odoo_product.find("input[name=product_id]").val(),  // the selected product-variant-id
    };
}

// HELPER FUNCTION TO PUSH TO THE DATALAYER
function push_to_datalayer (gtm_event_data) {
    if (Object.keys(gtm_event_data).length === 0) {
        console.log(`ERROR! gtm_event_data seems to be empty:\n${JSON.stringify(gtm_event_data, undefined, 2)}`)

    } else {
        console.log(`Push GTM Data Layer Event:\n${JSON.stringify(gtm_event_data, undefined, 2)}`);
        dataLayer.push({ ecommerce: null });  // Clear the previous ecommerce object.
        dataLayer.push(gtm_event_data);
    }
}

// Google Tag Manager Events
$(document).ready(function () {

    // --------------------------------------------------------------------------------
    // PRODUCT DETAIL VIEW (SINGLE PRODUCT PAGE)
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
        push_to_datalayer(event_data)
    }

    // --------------------------------------------------------------------------------
    // PRODUCT IMPRESSIONS VIEW (LIST-OF-PRODUCTS PAGE)
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
            console.log(`odoo_product_detail: ${odoo_product_detail}`);
            gtm_product_impressions.push(odoo_product_detail)
        });
    }
    console.log(`Product Impressions: ${JSON.stringify(gtm_product_impressions, undefined, 2)}`);
    // Add the collected product data to the Google Tag Manager dataLayer object
    if (gtm_product_impressions.length) {
        let event_data = {
            'event': 'fsonline.product_listing',
            'ecommerce': {
                'impressions': gtm_product_impressions
            }
        };
        console.log('PUSH !!!')
        push_to_datalayer(event_data)
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
            push_to_datalayer(event_data)
        } else {
            let event_data = {
                'event': 'fsonline.removeFromCart',
                'ecommerce': {
                    'remove': {
                        'products': [odoo_product_detail]
                    }
                }
            };
            push_to_datalayer(event_data)
        }

    });

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 1: CART
    // https://developers.google.com/tag-manager/enhanced-ecommerce#checkoutstep
    // HINT: This step will be skipped more often than not by the shop settings
    // ATTENTION: This step was disabled because you may come to the cart page without being in a checkout process!
    // --------------------------------------------------------------------------------
    if ($("#wsd_cart_page").length) {
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                let event_data = {
                    'event': 'fsonline.checkout.cart',
                    'ecommerce': {
                        'currencyCode': gtm_sale_order_data.currencyCode,
                        'checkout': {
                            'actionField': {
                                'step': 1
                            },
                            'products': gtm_sale_order_data.products
                        }
                    },
                }
                push_to_datalayer(event_data)
            }
        });
    }

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 2: USER DATA AND SHIPPING INFO
    // https://developers.google.com/tag-manager/enhanced-ecommerce#checkoutstep
    // --------------------------------------------------------------------------------
    // TODO: CHECKOUT-STEP_2-OPTION: SHIPPING METHOD (Skipped right now because rarely used!)
    // Step 1: Data of the Buyer
    if ($("#wsd_checkout_form").length) {
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                let event_data = {
                    'event': 'fsonline.checkout.userdata',
                    'ecommerce': {
                        'currencyCode': gtm_sale_order_data.currencyCode,
                        'checkout': {
                            'actionField': {
                                'step': 2
                            },
                            'products': gtm_sale_order_data.products
                        }
                    },
                }
                push_to_datalayer(event_data)
            }
        });
    }

    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 3: PAYMENT
    // CHECKOUT STEP 3 CHECKOUT OPTION: SELECTED PAYMENT METHOD
    // --------------------------------------------------------------------------------
    if ($("#payment_method").length) {
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                let active_acquirer = $('#payment_method li.active input[name=acquirer]').val() + '__' + $('#payment_method li.active .tab-acquirer-name').text();
                let event_data = {
                    'event': 'fsonline.checkout.paymentmethod',
                    'ecommerce': {
                        'checkout': {
                            'actionField': {
                                'step': 3,
                                'option': active_acquirer
                            },
                            'products': gtm_sale_order_data.products
                        }
                    },
                };
                push_to_datalayer(event_data)
            }
        });

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
        push_to_datalayer(event_data)
    });

});


// --------------------------------------------------------------------------------
// CHECKOUT STEP: PURCHASE
// ATTENTION: This would be Step 4 but Google Tag Manager accepts not 'step' option for 'purchase'.
//            As in the google example shop at
//            https://enhancedecommerce.appspot.com/checkout#confirmation!GA-checkoutStep:uaGtm
//            this has no step an the 'receipt' page (thank-you-page) will get the next step number (in our case 4)
// Triggered right before the final redirect to the payment provider
// TODO: Implement this in the "redirect to payment provider" page
// --------------------------------------------------------------------------------
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
            push_to_datalayer(event_data)
        }
    });
}
$("#wsd_pp_auto_submit_form.js_auto_submit_form form").on('submit', function(){
   pushGTMPurchaseEventOnSubmit("#wsd_pp_auto_submit_form .js_auto_submit_form form");
});


$(document).ready(function () {
    // --------------------------------------------------------------------------------
    // CHECKOUT STEP 4: CONFIRMATION / RECEIPT / THANK-YOU PAGE
    // HINT: This step might be missing if a custom redirect-after-pp-url was configured!
    // ATTENTION: As in the google example shop at
    //            https://enhancedecommerce.appspot.com/checkout#confirmation!GA-checkoutStep:uaGtm
    //            the products array should not be sent for this page
    // --------------------------------------------------------------------------------
    // TODO: Append the sale order data if any and send purchase cancellation request if the state of the so is
    //       e.g. cancelled
    if ($("div.wsd_confirmation_page").length) {
        let event_data = {
            'event': 'fsonline.confirmation_page_after_purchase',
            'ecommerce': {
                'checkout': {
                    'actionField': {
                        'step': 4,
                    },
                    "products": []
                }
            },
        };
        push_to_datalayer(event_data)
    }

});


