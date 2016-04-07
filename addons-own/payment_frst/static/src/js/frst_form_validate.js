$(document).ready(function () {

    // validate iban and bic
    //  http://jqueryvalidation.org/validate
    $("#frst").validate({
        rules: {
            frst_iban: {
                required: true,
                iban: true
            },
            frst_bic: {
                required: true,
                bic: true
            }
        },
    });

    // Make jquery validate work with a submit button instead of an submit input
    // http://stackoverflow.com/questions/11914626/jquery-validation-with-button-type-rather-than-submit-type-for-a-form
    $("#frst-submit-button").click(function(event) {
        $("#frst").submit();
    });
});
