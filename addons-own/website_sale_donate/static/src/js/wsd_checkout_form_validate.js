$(document).ready(function () {

    $( "#wsd_checkout_form" ).validate({

    });

    // Make jquery validate work with a submit button instead of an submit input
    // http://stackoverflow.com/questions/11914626/jquery-validation-with-button-type-rather-than-submit-type-for-a-form
    // TODO: Could be disabled because the "globally make submit buttons in forms work" will make this work too!
    $("#wsd_checkout_form_submit_button").click(function(event) {
        $("#wsd_checkout_form").submit();
    });

    // globally make submit buttons in forms work
    $("form button[type='submit']").click(function(event) {
        $("button[type='submit']").closest("form").submit();
    });

    // Auto Submit the payment provider form
    $(".js_auto_submit_form form").submit();

});
