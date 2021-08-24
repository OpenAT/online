// BEST TUTORIAL: https://www.simoahava.com/analytics/enhanced-ecommerce-guide-for-google-tag-manager

// HELPER FUNCTION TO READ PRODUCT DETAILS FROM PAGE HTML
// ------------------------------------------------------
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
// ----------------------------------------
function push_to_datalayer (gtm_event_data) {
    if (Object.keys(gtm_event_data).length === 0) {
        console.log(`ERROR! gtm_event_data seems to be empty:\n${JSON.stringify(gtm_event_data, undefined, 2)}`)
    } else {
        console.log(`Push GTM Data Layer Event:\n${JSON.stringify(gtm_event_data, undefined, 2)}`);
        dataLayer.push({ ecommerce: null });  // Clear the previous ecommerce object.
        dataLayer.push(gtm_event_data);
    }
}

// --------------------------------------------------------------------------------------------------------------------
// HELPER FUNCTIONS FOR THE DATALAYER EVENTS
// --------------------------------------------------------------------------------------------------------------------
function gtm_fsonline_product_detail () {
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
}

function gtm_fsonline_add_remove_cart () {
    $(".oe_website_sale form[action='/shop/cart/update']").submit( function() {
        let odoo_product_detail = get_odoo_product_details_for_gtm($("#product_detail.oe_website_sale"));
        let quantity = $(this).find("input[name=add_qty]").val();
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
}

function gtm_fsonline_checkout_cart_step_1 () {
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
}

function gtm_fsonline_checkout_userdata_step_2 () {
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

function gtm_fsonline_checkout_paymentmethod_step_3 () {
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
}

function gtm_fsonline_purchase (one_page_checkout=false) {
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
        if (one_page_checkout) {
            gtm_fsonline_checkout_cart_step_1();
            gtm_fsonline_checkout_userdata_step_2 ();
            gtm_fsonline_checkout_paymentmethod_step_3 ();
        }
        pushGTMPurchaseEventOnSubmit("#wsd_pp_auto_submit_form .js_auto_submit_form form");
    });
}

function gtm_fsonline_confirmation_page_after_purchase () {
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


$(document).ready(function () {

    gtm_fsonline_product_detail();
    gtm_fsonline_product_listing ();
    gtm_fsonline_add_remove_cart();

    // Check if this page is a OPC Page
    let $opc_page = $("section[name=one-page-checkout]");
    if ($opc_page.length) {
        console.log("!!! OPC PAGE DETECTED !!!");
        gtm_fsonline_purchase(true);
    } else {
        console.log("!!! REGULAR PAGE DETECTED !!!");
        gtm_fsonline_checkout_cart_step_1();
        gtm_fsonline_checkout_userdata_step_2 ();
        gtm_fsonline_checkout_paymentmethod_step_3 ();
        gtm_fsonline_purchase();
    }

    gtm_fsonline_confirmation_page_after_purchase();

});



