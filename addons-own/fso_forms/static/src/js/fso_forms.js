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

        },

        submitHandler: function(form) {
            form.submit();
          },
        invalidHandler: function(event, validator) {
            console.log('Form is invalid!');
            // Reenable the button for another submission try
            $("#fsoforms_submit_button").removeClass('submission-pending')
        }
    });
    
    // Submit the form by java script on click or keyup
    $('#fsoforms_submit_button').on('click keyup', function () {
        if ($("#fsoforms_submit_button").hasClass('submission-pending')) {
            // console.log('Submission Pending')
        }
        else {
            // console.log('Submit Form');
            // Lock the Button until validation fails (or form is submitted)
            $("#fsoforms_submit_button").addClass('submission-pending');
            $("form#fso_form.fso_form_validate").submit();
        }
    });

    // HINT: The debounce library is loaded in fso_base_website ;)
    // HINT: https://jqueryvalidation.org/documentation/#link-too-much-recursion
    // $('#fsoforms_submit_button').on('click keyup',
    //     $.debounce(400, function (event) {
    //         console.log('#fsoforms_submit_button debounced form submit');
    //         $("form#fso_form.fso_form_validate").submit();
    //     })
    // );

});
