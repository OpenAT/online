$(document).ready(function () {

    $( "#wsd_checkout_form" ).validate({

    });
    // Make jquery validate work with a submit button instead of an submit input
    // http://stackoverflow.com/questions/11914626/jquery-validation-with-button-type-rather-than-submit-type-for-a-form
    $("#wsd_checkout_form_submit_button").click(function(event) {
        $("#wsd_checkout_form").submit();
    });

});
