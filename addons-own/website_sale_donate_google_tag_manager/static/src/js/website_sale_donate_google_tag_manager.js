// BEST TUTORIAL: https://www.simoahava.com/analytics/enhanced-ecommerce-guide-for-google-tag-manager


function removeAllButLast(string, token) {
    let parts = string.split(token);
    if (parts[1]===undefined)
        return string;
    else
        return parts.slice(0,-1).join('') + token + parts.slice(-1)
}

// HELPER FUNCTION TO READ PRODUCT DETAILS FROM PAGE HTML
// ------------------------------------------------------
function get_odoo_product_details_for_gtm (odoo_product_html) {
    if (! odoo_product_html || ! odoo_product_html.length) {
        console.log('get_odoo_product_details_for_gtm() odoo_product_html is empty!');
        openerp.jsonRpc("/shop/sale_order_data_for_gtm/").then(function (gtm_sale_order_data) {
            if (gtm_sale_order_data && gtm_sale_order_data.products) {
                console.log('get_odoo_product_details_for_gtm() return product data from sale order!');
                return gtm_sale_order_data.products
            }
        });
        return {}
    }
    let $odoo_product = odoo_product_html;
    if (! $odoo_product instanceof jQuery) {
        console.log('odoo_product_html is not a jquery object!');
        $odoo_product = $(odoo_product_html)
    }
    // console.log(`odoo_product_html:\n${odoo_product_html.html()}`);

    let category = $odoo_product.find("input[name=cat_id]").val();
    if ( category === 'False') { category = false}
    let product_data = {
        'name': $odoo_product.find("[itemprop=name]").text() || $odoo_product.find("a[name=product_name]").text() || $odoo_product.find(".js_product").data("product-name"),
        // 'id': $odoo_product.find("div.js_product").data('product-template-id'),       // the product-template-id
        'price': $odoo_product.find("input[name=price_donate]").val() || $odoo_product.find("[itemprop=price]").text() || $odoo_product.find(".oe_currency_value").text(),
        'category': category || 'no-category',
        'variant': $odoo_product.find("input[name=product_id]").val() || $odoo_product.find("input.js_quantity").data("product-id"),  // the selected product-variant-id
    }

    // clean product-data values
    for (let key in product_data) {
        let val = product_data[key];
        // console.log(`PARSE key: ${key}, val: ${val}`);

        if (typeof val === 'string' || val instanceof String) {
            // Remove whitespace and newlines from all strings
            val = val.trim()
            // TODO: remove whitespace... e.g. for numbers like "22 444,23"
            // Convert price to a string with two digits
            if (val && key === 'price') {
                val = val.replaceAll(',', '.');
                val = removeAllButLast(val, '.');
                val = parseFloat(val).toFixed(2);
            }
        }

        if ( val && ['category', 'variant'].includes(key) && ! isNaN(parseInt(val)) ) {
            val = parseInt(val).toFixed(0);
        }

        // Store cleaned value
        product_data[key] = val;
    }

    return product_data;
}

// HELPER FUNCTION TO PUSH TO THE DATALAYER
// ----------------------------------------
function push_to_datalayer (gtm_event_data) {
    if (Object.keys(gtm_event_data).length === 0) {
        console.log(`ERROR! gtm_event_data seems to be empty:\n${JSON.stringify(gtm_event_data, undefined, 2)}`)
    } else {
        console.log(`PUSH GTM DATA LAYER EVENT:\n${JSON.stringify(gtm_event_data, undefined, 2)}`);
        //console.log(`PUSH GTM DATA LAYER EVENT:\n${JSON.stringify(gtm_event_data['event'], undefined, 2)}`);
        dataLayer.push({ ecommerce: null });  // Clear the previous ecommerce object.
        dataLayer.push(gtm_event_data);
    }
}

function is_opc_page () {
    return Boolean($("section[name=one-page-checkout]").length || $("#wrap.ppt_opc").length)
}

// --------------------------------------------------------------------------------------------------------------------
// HELPER FUNCTIONS FOR THE DATALAYER EVENTS
// --------------------------------------------------------------------------------------------------------------------
function gtm_fsonline_product_detail () {
    // console.log('gtm_fsonline_product_detail');

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
}

function gtm_fsonline_product_listing () {
    // console.log('gtm_fsonline_product_listing');

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
    //console.log(`Product Impressions: ${JSON.stringify(gtm_product_impressions, undefined, 2)}`);
    // Add the collected product data to the Google Tag Manager dataLayer object
    if (gtm_product_impressions.length) {
        let event_data = {
            'event': 'fsonline.product_listing',
            'ecommerce': {
                'impressions': gtm_product_impressions
            }
        };
        push_to_datalayer(event_data)
    }
}

function gtm_fsonline_add_remove_cart (product_html, forced_quantity) {
    // console.log(`gtm_fsonline_add_remove_cart: \n${product_html.html()}`);

    let quantity = forced_quantity || product_html.find("input[name=add_qty]").val() || "1";
    let odoo_product_detail = get_odoo_product_details_for_gtm(product_html);
    odoo_product_detail['quantity'] = parseFloat(quantity).toFixed(0);
    delete odoo_product_detail['category'];

    // Measure adding a product to a shopping cart by using an 'add' actionFieldObject
    // and a list of productFieldObjects.
    if (parseInt(quantity) > 0) {
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
}

function gtm_fsonline_checkout_cart_step_1 () {
    // console.log('gtm_fsonline_checkout_cart_step_1');

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
            } else {
                console.log('gtm_fsonline_checkout_cart_step_1; NO DATA FROM /shop/sale_order_data_for_gtm');
            }
        });
    }
}

function gtm_fsonline_checkout_userdata_step_2 () {
    // console.log('gtm_fsonline_checkout_userdata_step_2');

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
            } else {
                console.log('gtm_fsonline_checkout_userdata_step_2; NO DATA FROM /shop/sale_order_data_for_gtm');
            }
        });
    }
}

function gtm_fsonline_checkout_paymentmethod_step_3 () {
    // console.log('gtm_fsonline_checkout_paymentmethod_step_3');

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
            } else {
                console.log('gtm_fsonline_checkout_paymentmethod_step_3; NO DATA FROM /shop/sale_order_data_for_gtm');
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
}

function gtm_fsonline_purchase(){
    // console.log('gtm_fsonline_purchase');

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
        } else {
            console.log('gtm_fsonline_purchase; NO DATA FROM /shop/sale_order_data_for_gtm');
        }
    });
}

function gtm_fsonline_confirmation_page_after_purchase_step_4 () {
    // console.log('gtm_fsonline_confirmation_page_after_purchase');

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
}
// --------------------------------------------------------------------------------------------------------------------
// END: HELPER FUNCTIONS FOR THE DATALAYER EVENTS
// --------------------------------------------------------------------------------------------------------------------


// ----------------------
// PURCHASE EVENT HANDLER
// ----------------------
$(".js_auto_submit_form form").on('submit', function () {
    console.log("GOOGLE TAG MANAGER PURCHASE: .js_auto_submit_form form submit!")
    gtm_fsonline_purchase();
});


// ----------------------------------
// PRE PURCHASE FOR OPC PRODUCT PAGES
// ----------------------------------
// TODO: Since the Sale order is not ready yet we can not get the product data from the SO - so we need to extract
//       it from the html for OPC pages ...
//       For now we simply disabled these events to not return the event with an empty product list ...
// $("form.payment_opc_acquirer_form").on('submit', function () {
//     console.log("Purchase: form.payment_opc_acquirer_form submit!")
//     // For one-page-checkout pages
//     if ( is_opc_page() ) {
//         console.log('gtm_fsonline_purchase: one-page-checkout page detected');
//         gtm_fsonline_checkout_cart_step_1();
//         gtm_fsonline_checkout_userdata_step_2 ();
//         gtm_fsonline_checkout_paymentmethod_step_3 ();
//     }
// });
//
// $("form#wsd_checkout_form").on('submit', function () {
//     console.log("Purchase: form#wsd_checkout_form submit!")
//     // For one-page-checkout pages
//     if ( is_opc_page() ) {
//         console.log('gtm_fsonline_purchase: one-page-checkout page detected');
//         gtm_fsonline_checkout_cart_step_1();
//         gtm_fsonline_checkout_userdata_step_2 ();
//         gtm_fsonline_checkout_paymentmethod_step_3 ();
//     }
// });


// -----------------------------------------------
// GTM-EVENT-CHECKS on all pages (regular and opc)
// -----------------------------------------------
$(document).ready(function () {
    console.log("Google Tag Manager Webshop Events")

    if (typeof dataLayer !== 'undefined') {

        // Regular add-to-cart handler
        $(".oe_website_sale form[action='/shop/cart/update']").submit(function () {
            gtm_fsonline_add_remove_cart($(this));
        });

        // Shopping-Cart-Changes event handling
        $("input.js_quantity[data-line-id][data-product-id]").change(function () {
            let product_quantity = $(this).val();
            let $cart_line = $(this).closest("tr")
            gtm_fsonline_add_remove_cart($cart_line, product_quantity);
        })



        gtm_fsonline_confirmation_page_after_purchase_step_4();
        gtm_fsonline_product_detail();
        gtm_fsonline_product_listing();

        // GTM-EVENT-CHECKS for regular pages only
        // HINT: For OPC Pages these functions are called in gtm_fsonline_purchase() to only send gtm-checkout-events
        //       when purchasing the product (and not just when viewing the page)
        if (!is_opc_page()) {
            gtm_fsonline_checkout_cart_step_1();
            gtm_fsonline_checkout_userdata_step_2();
            gtm_fsonline_checkout_paymentmethod_step_3();
        }

    } else {
        console.log("WARNING: Google Tag Manager variable 'dataLayer' is not defined!")
    }

});
