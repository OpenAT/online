$(document).ready(function () {

    // Set Suggested Price by Buttons dynamically on click
    // ---------------------------------------------------
    // HINT: The initial 'btn-primary' element is set by the qweb template
    let $price_donate = $("#price_donate");
    let $price_suggested = $(".price_donate_suggested");
    let $price_suggested_donation_buttons = $('.donation_button:not(.donation_button_snippets)');

    $price_suggested.on("click", function (ev1) {
        // Copy the button value to the <input id="price_donate"> value
        $price_donate.val( $(this).data("price") ).trigger('change');

        // ACTIVE BUTTON FOR THE NEW DONATION BUTTON LAYOUTS

        // remove class 'btn-primary' from all buttons
        $price_suggested_donation_buttons.removeClass('btn-primary').addClass('btn-default');

        // add 'btn-primary' to the currently clicked button but only if it is no snippet area
        if ($(this).hasClass('donation_button') && ! $(this).hasClass('donation_button_snippets')) {
            $(this).removeClass('btn-default').addClass('btn-primary');
        }

        // remove btn-primary from the input field if set
        $price_donate.removeClass('btn-primary')

    });

    // remove class 'btn-primary' from all buttons if something is typed in the <input id="price_donate">
    $price_donate.on("keypress", function (ev1) {
        $price_suggested_donation_buttons.removeClass('btn-primary').addClass('btn-default');
        $price_donate.addClass('btn-primary');
    });
    // ------------------------------


    // START: RECOMPUTE PRICE SUGGESTED FOR PAYMENT INTERVALS
    if ($("#payment_intervals").data('auto-recompute-price-donate')) {

        // RADIO BUTTONS
        $("input[name='payment_interval_id']").on("click", function (ev) {
            if ($(this).attr('data-checked-before') === '1') {
                // console.log('INTERVAL ALREADY CHECKED')
            } else {
                let former_payment_interval = $("input[name='payment_interval_id'][data-checked-before='1']");
                let former_months = parseInt(former_payment_interval.attr('data-payment-interval-length-in-months'));
                let $price_donate = $("input#price_donate");
                let former_price_donate_value = parseFloat($price_donate.attr('data-value-float'));
                if (!former_price_donate_value) {
                    // console.log('Fallback to price_donate value');
                    former_price_donate_value = parseFloat($("input#price_donate").val());
                }
                if (!former_price_donate_value) {
                    former_price_donate_value = parseFloat($("b.oe_price>span.oe_currency_value")[0].innerText);
                }
                let current_months = parseInt($(this).attr('data-payment-interval-length-in-months'));
                former_payment_interval.removeAttr('data-checked-before');
                // console.log('former_payment_interval: ', former_payment_interval.attr('data-payment-interval-external-id'));
                // console.log('former_months', former_months, 'former_price_donate_value', former_price_donate_value, 'current_months', current_months);
                if (former_months && former_price_donate_value && current_months) {
                    let current_price_donate_value = former_price_donate_value / former_months * current_months;
                    // console.log('current_price_donate_value', current_price_donate_value);
                    let current_price_donate_value_rounded = Math.round((current_price_donate_value + Number.EPSILON) * 100) / 100
                    $("input#price_donate").val(current_price_donate_value_rounded).trigger("change");
                    $("input#price_donate").attr('data-value-float', current_price_donate_value);
                    $("b.oe_price>span.oe_currency_value")[0].innerText = current_price_donate_value_rounded;
                }
            }
            $(this).attr('data-checked-before', '1');
            // console.log('current_payment_interval: ', $(this).attr('data-payment-interval-external-id'));
        })

        // SELECTION LIST
        $("select[name='payment_interval_id']").on("click change input", function (ev) {
            let $selected_option = $("select[name='payment_interval_id'] option:selected")
            if ($selected_option.attr('data-checked-before') === '1') {
                // console.log('INTERVAL ALREADY SELECTED')
            } else {
                let former_payment_interval = $("select[name='payment_interval_id'] option[data-checked-before='1']");
                let former_months = parseInt(former_payment_interval.attr('data-payment-interval-length-in-months'));
                let $price_donate = $("input#price_donate");
                let former_price_donate_value = parseFloat($price_donate.attr('data-value-float'));
                if (!former_price_donate_value) {
                    // console.log('Fallback to price_donate value');
                    former_price_donate_value = parseFloat($("input#price_donate").val());
                }
                if (!former_price_donate_value) {
                    former_price_donate_value = parseFloat($("b.oe_price>span.oe_currency_value")[0].innerText);
                }
                let current_months = parseInt($selected_option.attr('data-payment-interval-length-in-months'));
                former_payment_interval.removeAttr('data-checked-before');
                // console.log('former_payment_interval: ', former_payment_interval.attr('data-payment-interval-external-id'));
                // console.log('former_months', former_months, 'former_price_donate_value', former_price_donate_value, 'current_months', current_months);
                if (former_months && former_price_donate_value && current_months) {
                    let current_price_donate_value = former_price_donate_value / former_months * current_months;
                    // console.log('current_price_donate_value', current_price_donate_value);
                    let current_price_donate_value_rounded = Math.round((current_price_donate_value + Number.EPSILON) * 100) / 100
                    $("input#price_donate").val(current_price_donate_value_rounded).trigger("change");
                    $("input#price_donate").attr('data-value-float', current_price_donate_value);
                    $("b.oe_price>span.oe_currency_value")[0].innerText = current_price_donate_value_rounded;
                }
            }
            $selected_option.attr('data-checked-before', '1');
            // console.log('current_payment_interval: ', $(this).attr('data-payment-interval-external-id'));
        })

        // REMOVE THE FLOAT VALUE ON CHANGES OF THE price-donate value
        // HINT: Make sure all .val(xxx) calls are changed to .val(xxx).trigger("change") to make this work
        $("input#price_donate").on("propertychange change click keyup input paste", function (ev) {
            $(this).removeAttr('data-value-float');
            // console.log('REMOVE data-value-float');
        })
    }
    // END: RECOMPUTE PRICE SUGGESTED FOR PAYMENT INTERVALS

    // Click radio input of the selected payment interval on first load of the page
    $("input[name='payment_interval_id'][checked]").ready(function () {
        //console.log('On Load of Payment Intervalls');
        $("input[name='payment_interval_id'][checked]").trigger('click');
    });
    // Click select option of the selected payment interval on first load of the page
    $("select[name='payment_interval_id']").ready(function () {
        //console.log('On Load of Payment Intervalls Selection');
        $("select[name='payment_interval_id'] option:selected").trigger('change');
    });

    // Hide all tabs and related tab-content that are not recurring if recurring payment is selected
    let $radio_payint = $("input[name='payment_interval_id']");
    $radio_payint.on("click", function (ev) {
        if ( $(this).attr('data-payment-interval-external-id') != 'website_sale_donate.once_only' ) {

            // hide all acquirer tabs that do not work with recurring transactions if any
            $( "[data-recurring-transactions='False']").addClass('hidden');

            // Check if active tab is now hidden and if 'click' the next non hidden tab
            if ( !($('#payment_method li.active:not(.hidden)').length) ) {
                //console.log('No Tab Active');
                // Select next non hidden tabs (li) link (a) and click it
                $('#payment_method li:not(.hidden) a[role="tab"]:first').trigger('click');
            };

        } else {
            // Unhide all tabs and its content if no recurring payment interval is selected
            $( "[data-recurring-transactions='False']").removeClass('hidden');
        }
    });
    // Hide all tabs and related tab-content that are not recurring if recurring payment is selected
    let $select_payint = $("select[name='payment_interval_id']");
    $select_payint.on("change", function (ev) {
        let data_payment_interval_external_id = $( "select[name='payment_interval_id'] option:selected" ).attr('data-payment-interval-external-id');
        if ( data_payment_interval_external_id != 'website_sale_donate.once_only' ) {

            // hide all acquirer tabs that do not work with recurring transactions if any
            $( "[data-recurring-transactions='False']").addClass('hidden');

            // Check if active tab is now hidden and if 'click' the next non hidden tab
            if ( !($('#payment_method li.active:not(.hidden)').length) ) {
                //console.log('No Tab Active');
                // Select next non hidden tabs (li) link (a) and click it
                $('#payment_method li:not(.hidden) a[role="tab"]:first').trigger('click');
            }

        } else {
            // Unhide all tabs and its content if no recurring payment interval is selected
            $( "[data-recurring-transactions='False']").removeClass('hidden');
        }
    });

    // Select (check) radio input tag of the acquirer tab on tab click
    let $payment = $("#payment_method");
    $('#payment_method a[role="tab"]').on("click", function (e) {

        // Set tab-related hidden radio-input-tag to checked
        $('ul[role="tablist"]').find("input[name='acquirer']:checked").removeAttr('checked');
        $( this ).find("input[name='acquirer']").prop('checked', true);

        // Disable the other input tags (payment methods) (maybe not needed)
        let payment_id = $( this ).find("input[name='acquirer']").val();
        $("div.tab-content div[data-id] input", $payment).attr("disabled", "true");
        $("div.tab-content div[data-id='"+payment_id+"'] input", $payment).removeAttr("disabled");
    });

    // Make the stuff from website_sale website_sale_payment.js work with our acquirer tabs if not OPC
    // When clicking on payment button: create the tx using json then continue to the acquirer
    $payment.on("click", 'button[type="submit"],button[name="submit"]', function (ev) {
        console.log('Mike Acquirer Submit Button: preventDefault stopPropagation')
        ev.preventDefault();
        ev.stopPropagation();
        let $form = $(ev.currentTarget).parents('form');
        let acquirer_id = $(ev.currentTarget).parents('div.acquirer_button_not_opc').first().data('id');
        if (!acquirer_id) {
            console.log('Mike: No acquirer ID');
            return false;
        }
        openerp.jsonRpc('/shop/payment/transaction/' + acquirer_id, 'call', {}).then(function (data) {

            // Now the controller returns html content that will replace the previous form content
            // HINT: This renders the button again and would eventually create a new Payment TX if something is wrong
            console.log('Mike: /shop/payment/transaction/ REPLACE PAY-NOW-BUTTON FORM DATA:' + data);
            $form.html(data);

            // Submit the form
            console.log('Mike: SU/shop/payment/transaction/ SUBMIT PAY-NOW-BUTTON FORM');
            $form.submit();
        });
    });


    // Equal content height tab boxes
    let maxHeight=0;
    $(".tab-content.tab-equal-heights .tab-pane").each(function(){
        let height = $(this).height();
        maxHeight = height>maxHeight?height:maxHeight;
    });
    $(".tab-content.tab-equal-heights").height(maxHeight);

    // DISABLED: Update Page on Delivery-Method Change
    // HINT: Disabled because it is better to press the next button than the auto submit of the form
    //$("bla bla").find("input[name='delivery_type']").click(function (ev) {
    //    $(ev.currentTarget).parents('form').submit();
    //});
});

// DISABLED BECAUSE IT MAY INTERFERE WITH THE IFRAMERESIZER IF AN ELEMENT IS IN FOCUS BEFORE THE CALCULATION
// $(window).load(function() {
//     console.log("LOADED IT");
//     let $price_donate = $("#price_donate");
//     let $price_suggested = $(".price_donate_suggested");
//     if ($price_donate.length && $price_suggested.length) {
//         console.log("FOUND IT");
//         // Focus on the input field if the current value does not fit to any suggested button value
//         // Get the suggested values of all buttons and snippet fields
//         let suggested_button_values = [];
//         $price_suggested.each(function(){ suggested_button_values.push( $(this).data("price") )});
//         // Set the <input id="price_donate"> in focus if none of the buttons match
//         if ( $price_donate.val() && !suggested_button_values.includes($price_donate.val()) ) {
//             console.log("Focus on it");
//             $price_donate.focus();
//         }
//     }
// });
