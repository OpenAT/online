$(document).ready(function () {

    $( "#wsd_checkout_form" ).validate({

        // Try to prevent multiple submits on successful validation
        // https://www.fetchdesigns.com/prevent-duplicate-form-submission-jquery-validate/
        // https://stackoverflow.com/questions/45562409/prevent-double-clicking-when-using-jquery-validate-submithandler
        // https://stackoverflow.com/questions/5996950/jquery-validate-plugin-prevent-double-submit-on-validation

        submitHandler: function (form) {
            console.log('#wsd_checkout_form submit handler');
            // Prevent double submission
            if (!this.beenSubmitted) {
                this.beenSubmitted = true;
                console.log('#wsd_checkout_form submitting the form');
                form.submit();
            }
            else {
                console.log('#wsd_checkout_form SUPPRESSED MULTI SUBMIT!');
            }
        }

    });

    // Make jquery validate work with a submit button instead of an submit input
    // http://stackoverflow.com/questions/11914626/jquery-validation-with-button-type-rather-than-submit-type-for-a-form
    $("#wsd_checkout_form_submit_button").click(function(event) {
        $("#wsd_checkout_form").submit();
    });

    // DISABLED: globally make submit buttons in forms work
    //$("form button[type='submit']").click(function(event) {
    //    $("button[type='submit']").closest("form").submit();
    //});

    // Auto Submit the payment provider form
    //$(".js_auto_submit_form form").submit();

    // let auto_submit_form = $("#wsd_pp_auto_submit_form.js_auto_submit_form form");
    // if (auto_submit_form.length) {
    //     auto_submit_form.submit();
    // }

    $("#wsd_pp_auto_submit_form.js_auto_submit_form form").submit()


});
