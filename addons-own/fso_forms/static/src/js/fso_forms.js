/**
 * Created by mkarrer on 21.12.16.
 */

$(document).ready(function () {

    // JQUERY-VALIDATE SETTINGS
    $( "form#fso_form.fso_form_validate" ).validate({
        // EXAMPLES FOR CUSTOM/ADDITIONAL RULES CONFIGURATION
        rules: {
            // email: {
            //     required: function (element) {
            //         return $("#newsletter_web").is(":checked");
            //     }
            // },
            //
            // birthdate_web: {
            //     required: function (element) {
            //         // This makes the birthdate_web field mandatory if donation_deduction_optout_web is NOT checked
            //         // HINT: if "mandatory" is checked in apf fields the field will ALWAYS be mandatory
            //         //       by server side validation!
            //         // console.log('TEST ' + !$("#donation_deduction_optout_web").is(':checked') );
            //         return !$("#donation_deduction_optout_web").is(':checked');
            //     }
            // }

        }
    });

    // SUBMIT-BUTTON BY JS
    // HINT: Submit only after document ready and by java script
    // HINT: This is also needed to make jquery-validate work with a submit button instead of an submit input
    //       http://stackoverflow.com/questions/11914626/jquery-validation-with-button-type-rather-than-submit-type-for-a-form
    $("#apf_submit_button").click(function(event) {
        $("form#fso_form.fso_form_validate").submit();
    });

});
