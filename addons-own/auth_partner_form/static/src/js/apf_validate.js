/**
 * Created by mkarrer on 21.12.16.
 */
$(document).ready(function () {

    // Enable jquery validate for the form
    $( "#auth_partner_form" ).validate({
        // Special rule to make birthdate_web mandatory if donation_deduction (Spendenabsetzbarkeit) is selected
        rules: {
            birthdate_web: {
                required: function (element) {
                    var radio;
                    var list;
                    var test;
                    radio = $("input:radio[name='donation_deduction']:checked").val();
                    list = $("#donation_deduction option:checked").val();
                    test = radio || list || '';
                    // console.log(radio);
                    // console.log(list);
                    // console.log(test);
                    return test === "donation_deduction";
                }
            }
        }
    });

    // Make jquery validate work with a submit button instead of an submit input
    // http://stackoverflow.com/questions/11914626/jquery-validation-with-button-type-rather-than-submit-type-for-a-form
    $("#apf_submit_button").click(function(event) {
        $("#auth_partner_form").submit();
    });

});