/**
 * Created by michaelkarrer81@gmail.com
 * Check if a bpk number can be found if all input fields are filled and have the correct length and format
 * Debounce the bpk calls so that there are at least 3 seconds before the next request is made after data changes
 */

// https://github.com/cowboy/jquery-throttle-debounce
// http://benalman.com/projects/jquery-throttle-debounce-plugin/
// https://stackoverflow.com/questions/14042193/how-to-trigger-an-event-in-input-text-after-i-stop-typing-writing
// https://stackoverflow.com/questions/39196323/run-ajax-request-only-when-user-has-filled-in-all-required-fields

// TODO add zip field
// TODO add ddow field
// Initialize global variables
var firstname_start = '' ;
var lastname_start = '' ;
var birthdate_web_start = '' ;

var firstname_start_2 = '' ;
var lastname_start_2 = '' ;
var birthdate_web_start_2 = '' ;

// apf_bpk_status_box only matched if not in edit mode
var apf_box = '';

// Initialize ladda for the apf_bpk_status_box div element
var apf_ladda = '';

// Get the span element for ladda loading message
var apf_loading = '';

// Get the span element for the check_bpk() message
var apf_message = '';


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


// TODO: add zip field
// TODO add ddow field
// Check content of form input fields and set BPK-Status-Box accordingly
function apf_check_bpk( event ) {
    // Get data from input fields
    var firstname = $("#firstname").val();
    var lastname = $("#lastname").val();
    var birthdate_web = $("#birthdate_web").val();
    var ddow = $("#donation_deduction_optout_web").prop('checked');

    // Check BPK Request if ddow is not set, at least one field changed and required fields are ok
    if (!ddow &&
        firstname.length >= 3 &&
        lastname.length >= 3 &&
        moment(birthdate_web, "DD.MM.YYYY", true).isValid() &&
        (firstname !== firstname_start || lastname !== lastname_start || birthdate_web !== birthdate_web_start)
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
                // BPK Request Success
                console.log("BPK Request Success");
                apf_ladda.stop();
                apf_loading.hide();
                apf_box.removeClass("bg-info bg-success bg-warning").addClass("bg-success");
                apf_message.text(bpk_ok[1].message);
                apf_message.show();
                apf_box.show();
            }
            else {
                // BPK Request Error
                console.log("BPK Request Error");
                apf_ladda.stop();
                apf_loading.hide();
                apf_box.removeClass("bg-info bg-success bg-warning").addClass("bg-warning");
                apf_message.text(bpk_ok[1].message);
                apf_message.show();
                apf_box.show();
            }
        }, function (error) {
            // BPK Request Exception
            console.log("BPK Request Exception");
            apf_box.hide();
            apf_ladda.stop();
            apf_loading.hide();
            apf_message.hide();
            apf_message.text("");
        }).then(function () {
            // Store field values for comparision on subsequent calls!
            firstname_start = firstname;
            lastname_start = lastname;
            birthdate_web_start = birthdate_web;
        })
    }

}

function apf_box_hide_or_spinner( event ) {
    // Get data from input fields
    var firstname = $("#firstname").val();
    var lastname = $("#lastname").val();
    var birthdate_web = $("#birthdate_web").val();
    var ddow = $("#donation_deduction_optout_web").prop('checked');

    // Hide BPK-Status-Box if ddow is set or mandatory-field-values are missing
    if ($(".apf_bpk_status_box").is(':visible') &&
        (ddow || !firstname || !lastname || !birthdate_web)
    ) {
        console.log("Hide BPK-Status-Box!");
        apf_box.hide();
        apf_box.removeClass("bg-info bg-success bg-warning").addClass("bg-info");
        apf_message.hide();
        apf_loading.hide();
        apf_ladda.stop();
    }
    // Start a spinner if data has changed and a bpk request is expected to be made
    else if (!ddow &&
        firstname.length >= 3 &&
        lastname.length >= 3 &&
        moment(birthdate_web, "DD.MM.YYYY", true).isValid() &&
        (firstname !== firstname_start_2 || lastname !== lastname_start_2 || birthdate_web !== birthdate_web_start_2)
    ){
        console.log("Start BPK-Status-Box Spinner!");
        apf_box.removeClass("bg-info bg-success bg-warning").addClass("bg-info");
        apf_message.hide();
        apf_loading.show();
        apf_box.show();
        apf_ladda.start();
    }

    // Store field values for comparision on subsequent calls!
    firstname_start_2 = firstname;
    lastname_start_2 = lastname;
    birthdate_web_start_2 = birthdate_web;
}


// BPK-Status-Box for the /meine-daten form
$(document).ready(function ( event ) {

    // TODO: ADD ZIP to the fields
    // TODO add ddow field
    // Only run this if the snippet is located on this page and all relevant fields exists ( .length = exists )
    if ($('.snippet_apf_bpk_status').length && $("html:not([data-editable=\"1\"]) .apf_bpk_status_box").length &&
        $('#firstname').length && $('#lastname').length && $('#birthdate_web').length){
        console.log("BPK-Status live check started!");

        // apf_bpk_status_box only matched if not in edit mode
        apf_box = $("html:not([data-editable=\"1\"]) .apf_bpk_status_box");

        // Initialize ladda for the apf_bpk_status_box div element
        apf_ladda = Ladda.create(document.querySelector( ".apf_bpk_status_box" ));

        // Get the span element for ladda loading message
        apf_loading = $(".apf_bpk_status_box_loading");

        // Get the span element for the check_bpk() message
        apf_message = $(".apf_bpk_status_box_message");

        // Run apf_check_bpk() for the initial values
        // TODO: only run initially if there is no status message box "apf_messages"
        console.log("Run apf_box_hide_or_spinner() for initial values!");
        apf_box_hide_or_spinner(event);
        console.log("Run apf_check_bpk() for initial values!");
        apf_check_bpk( event );

        // Get initial values from the form input fields
        firstname_start = $("#firstname").val() || '' ;
        lastname_start = $("#lastname").val() || '' ;
        birthdate_web_start = $("#birthdate_web").val() || '' ;

        firstname_start_2 = $("#firstname").val() || '' ;
        lastname_start_2 = $("#lastname").val() || '' ;
        birthdate_web_start_2 = $("#birthdate_web").val() || '' ;

        // HIDE THE STATUS BOX OR START THE SPINNER
        // HINT: The box should start the spinner or get hidden way faster than the do check_bpk() requests
        $('#firstname, #lastname, #birthdate_web, #donation_deduction_optout_web').on('click keyup',
            $.debounce(800, function (event) {
                console.log("Run apf_box_hide_or_spinner()!");
                apf_box_hide_or_spinner(event);
            })
        );

        // RUN CHECK BPK 3 SECONDS AFTER LAST INPUT
        // Check all text input fields of the auth partner form (/meine-daten) for changes in the input fields
        // ATTENTION: debounce will only start the function apf_check_bpk() after no changes to the input fields for 2000ms
        //            On every keyup it will wait again for 4000ms until the moment where there was no keyup for 4000ms.
        //            Only then it will execute the function apf_check_bpk(...)
        $('#firstname, #lastname, #birthdate_web, #donation_deduction_optout_web').on('click keyup',
                // Check BPK
                // HINT: Will do a BPK-Request only if relevant field-data changed and stayed unchanged for 2 seconds
                $.debounce( 3000, function ( event ) {
                    console.log("Run apf_check_bpk()!");
                    apf_check_bpk( event );
                })
            );


    }

});
