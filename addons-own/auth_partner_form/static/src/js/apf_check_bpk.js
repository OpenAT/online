/**
 * Created by michaelkarrer81@gmail.com
 * Check if a bpk number can be found if all input fields are filled and have the correct length and format
 * Debounce the bpk calls so that there are at least 3 seconds before the next request is made after data changes
 */

// https://github.com/cowboy/jquery-throttle-debounce
// http://benalman.com/projects/jquery-throttle-debounce-plugin/
// https://stackoverflow.com/questions/14042193/how-to-trigger-an-event-in-input-text-after-i-stop-typing-writing
// https://stackoverflow.com/questions/39196323/run-ajax-request-only-when-user-has-filled-in-all-required-fields

// TODO: Add zip field
// call '/check_bpk' route of odoo
function check_bpk( event, firstname, lastname, birthdate ) {
    console.log("Jetzt wird BPK abgefragt: " + firstname + " " + lastname + " " + birthdate);

    return openerp.jsonRpc("/check_bpk", 'call', {
        'firstname': firstname,
        'lastname': lastname,
        'birthdate': birthdate
    });
}

// TODO add zip field
// Initialize global variables before definition of apf_check_bpk()
var firstname_start = '' ;
var lastname_start = '' ;
var birthdate_web_start = '' ;

// TODO: add zip field
// Check content of form input fields and set BPK-Status-Box accordingly
function apf_check_bpk( event ) {
    // Get data from input fields
    var firstname = $("#firstname").val();
    var lastname = $("#lastname").val();
    var birthdate_web = $("#birthdate_web").val();
    var ddow = $("#donation_deduction_optout_web").prop('checked');

    // Hide BPK-Status-Box if ddow is set or fields have changed or one of them is empty
    if (ddow ||
        !firstname || firstname !== firstname_start ||
        !lastname || lastname !== lastname_start ||
        !birthdate_web || birthdate_web !== birthdate_web_start
    ) {
        console.log("Hide BPK-Status-Box!");
        $("html:not([data-editable=\"1\"]) .apf_bpk_status_message").hide();
    }

    // Check BPK Request if all ddow is not set, at least one field changed and required fields are ok
    if (!ddow &&
        firstname.length >= 3 &&
        lastname.length >= 3 &&
        moment(birthdate_web, "DD.MM.YYYY", true).isValid() &&
        (firstname !== firstname_start || lastname !== lastname_start || birthdate_web !== birthdate_web)
    ) {

        // Convert birthdate to the correct format for zmr requests
        var birthdate_web_for_zmr = moment(birthdate_web, "DD.MM.YYYY", true);
        birthdate_web_for_zmr = birthdate_web_for_zmr.format("YYYY-MM-DD");

        // Run check_bpk
        check_bpk( event, firstname, lastname, birthdate_web_for_zmr ).then(function (bpk_ok) {
            console.log('bpk_ok[0]: ' + bpk_ok[0]);
            console.log('bpk_ok[1]: ' + bpk_ok[1]);
            console.log('bpk_ok[1].state: ' + bpk_ok[1].state);
            console.log('bpk_ok[1].message: ' + bpk_ok[1].message);
            if (bpk_ok[0]) {
                $(".apf_bpk_status_message.bpk_success").show()
            }
            else {
                $(".apf_bpk_status_message.bpk_error").show()
            }
        }, function (error) {
                console.log("ERROR: " + error);
                $("html:not([data-editable=\"1\"]) .apf_bpk_status_message").hide();
        }).then(function () {
            // Store the values to check later if they have changed
            console.log('Store field values for comparrisson on subsequent calls!');
            firstname_start = firstname;
            lastname_start = lastname;
            birthdate_web_start = birthdate_web;
        })
    }

}

// BPK-Status-Box for the /meine-daten form
$(document).ready(function ( event ) {

    // TODO: ADD ZIP to the fields
    // TODO: Nicer Animations and button animtions with spinner

    // Only run this if the snippet is located on this page and all relevant fields exists
    if ($('.snippet_apf_bpk_status').length &&
        $('#firstname').length && $('#lastname').length && $('#birthdate_web').length){
        console.log("BPK-Status live check started!");

        // Get initial values from the form input fields
        firstname_start = $("#firstname").val() || '' ;
        lastname_start = $("#lastname").val() || '' ;
        birthdate_web_start = $("#birthdate_web").val() || '' ;

        // Run apf_check_bpk() for the initial values
        console.log("Run apf_check_bpk() for initial values!");
        apf_check_bpk( event );

        // TODO: Separate the hide function from the show function: Hide should happen immediately after input
        //       data of any of the relevant fields has changed! (in opposite to be delayed for 2000ms)

        // Check all text input fields of the auth partner form (/meine-daten) for changes in the input fields
        // ATTENTION: debounce will only start the function apf_check_bpk() after no changes to the input fields for 2000ms
        //            On every keyup it will wait again for 4000ms until the moment where there was no keyup for 4000ms.
        //            Only then it will execute the function apf_check_bpk(...)
        $('#firstname, #lastname, #birthdate_web').keyup(
            $.debounce( 2000,
                function ( event ) {
                    apf_check_bpk( event );
                }
            ));
    }


});
