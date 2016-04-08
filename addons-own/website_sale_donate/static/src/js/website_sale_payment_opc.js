$(document).ready(function () {

    // Set Suggested Price
    var $price_donate = $("#price_donate");
    var $price_suggested = $(".price_donate_suggested");
    $price_suggested.on("click", function (ev1) {
        $price_donate.val( $(this).val() );
    });

    // hide all tabs that are not recurring if recurring payment is selected
    var $radio_payint = $("input[name='payment_interval_id']");
    $radio_payint.on("click", function (ev) {
        if ( $(this).attr('data-payment-interval-external-id') != 'website_sale_donate.once_only' ) {
            // hide all acquirer tabs that do not work with recurring transactions if any
            $( "[data-recurring-transactions='False']").addClass('hidden');
            // Todo Check if active tab is now hidden and if 'click' the next non hidden tab
        } else {
            $( "[data-recurring-transactions='False']").removeClass('hidden');
        }
    });

    // Check radio input tag of the acquirer tab on tab click
    var $payment = $("#payment_method");
    $('#payment_method a[role="tab"]').on("click", function (e) {
        // Set child radio input tag to checked
        $('ul[role="tablist"]').find("input[name='acquirer']:checked").removeAttr('checked');
        $( this ).find("input[name='acquirer']").prop('checked', true);

        // Disable all other input tags of other payment methods
        var payment_id = $( this ).find("input[name='acquirer']").val();
        $("div.tab-content div[data-id] input", $payment).attr("disabled", "true");
        $("div.tab-content div[data-id='"+payment_id+"'] input", $payment).removeAttr("disabled");
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
