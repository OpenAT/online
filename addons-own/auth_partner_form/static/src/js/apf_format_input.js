/**
 * Created by mkarrer on 21.12.16.
 */
$(document).ready(function () {

    // Format the fs_ptoken code in rows of three with uppercase letters e.g. A4F - 3GH - 296
    // https://webdesign.tutsplus.com/tutorials/auto-formatting-input-value--cms-26745
    var $token_input = $( "#auth_partner_form input[name='fs_ptoken']" );
    $token_input.on( "keyup", function ( event ) {

        // Do nothing if input field is empty
        var selection = window.getSelection().toString();
        if ( selection !== '' ) {
            return;
        }
        // Do nothing if the user navigates by keyboard cursor keys
        if ( $.inArray( event.keyCode, [38,40,37,39] ) !== -1 ) {
            return;
        }

        // Get the value of the input field and convert to upper case
        var $this = $( this );
        var input = $this.val();
        input = input.toUpperCase();

        // Sanitize input (Replace all characters that are not(^) 0-9 and A-Z with Nothing)
        // http://regexr.com
        input = input.replace(/([^0-9A-Z])/g, "");

        // Split input in junks of 3
        var split = 3;
        var chunks = [];
        for (var i = 0, len = input.length; i < len; i += split) {
            chunks.push( input.substr( i, split ) );
        }

        // Return the processed input
        $this.val(function() {
            return chunks.join(" - ");
        });
    });

});


