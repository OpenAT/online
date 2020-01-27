$(document).ready(function () {

    // Set Suggested Price by Buttons
    var $price_donate = $("#price_donate");
    var $price_suggested = $(".price_donate_suggested");
    var $price_suggested_donation_button = $price_suggested.filter('.donation_button');
    $price_suggested.on("click", function (ev1) {
        $price_donate.val( $(this).data("price") );

        // ACTIVE BUTTON FOR THE NEW DONATION BUTTON LAYOUTS
        $price_suggested_donation_button.removeClass('btn-primary').addClass('btn-default');
        if ($(this).hasClass('donation_button')) {
            $(this).removeClass('btn-default').addClass('btn-primary');
        }

    });


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
    var $radio_payint = $("input[name='payment_interval_id']");
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
    var $select_payint = $("select[name='payment_interval_id']");
    $select_payint.on("change", function (ev) {
        var data_payment_interval_external_id = $( "select[name='payment_interval_id'] option:selected" ).attr('data-payment-interval-external-id');
        if ( data_payment_interval_external_id != 'website_sale_donate.once_only' ) {

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

    // Select (check) radio input tag of the acquirer tab on tab click
    var $payment = $("#payment_method");
    $('#payment_method a[role="tab"]').on("click", function (e) {

        // Set tab-related hidden radio-input-tag to checked
        $('ul[role="tablist"]').find("input[name='acquirer']:checked").removeAttr('checked');
        $( this ).find("input[name='acquirer']").prop('checked', true);

        // Disable the other input tags (payment methods) (maybe not needed)
        var payment_id = $( this ).find("input[name='acquirer']").val();
        $("div.tab-content div[data-id] input", $payment).attr("disabled", "true");
        $("div.tab-content div[data-id='"+payment_id+"'] input", $payment).removeAttr("disabled");
    });

    // Make the stuff from website_sale website_sale_payment.js work with our acquirer tabs if not OPC
    // When clicking on payment button: create the tx using json then continue to the acquirer
    $payment.on("click", 'button[type="submit"],button[name="submit"]', function (ev) {
        console.log('Mike Acquirer Submit Button: preventDefault stopPropagation')
        ev.preventDefault();
        ev.stopPropagation();
        var $form = $(ev.currentTarget).parents('form');
        var acquirer_id = $(ev.currentTarget).parents('div.acquirer_button_not_opc').first().data('id');
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
    var maxHeight=0;
    $(".tab-content.tab-equal-heights .tab-pane").each(function(){
        var height = $(this).height();
        maxHeight = height>maxHeight?height:maxHeight;
    });
    $(".tab-content.tab-equal-heights").height(maxHeight);

    // DISABLED: Update Page on Delivery-Method Change
    // HINT: Disabled because it is better to press the next button than the auto submit of the form
    //$("bla bla").find("input[name='delivery_type']").click(function (ev) {
    //    $(ev.currentTarget).parents('form').submit();
    //});
});


