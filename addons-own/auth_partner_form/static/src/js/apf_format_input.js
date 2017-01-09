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
        var input = input.toUpperCase();

        // Sanitize input (Replace all characters that are not(^) 0-9 and A-Z with Nothing)
        // http://regexr.com
        var input = input.replace(/([^0-9A-Z])/g, "");

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
    })

    // Format the birthday date-input pickdate.js and jquery
    // http://jqueryui.com/datepicker/
    // https://codepen.io/amsul/pen/LhlAK
    // http://amsul.ca/pickadate.js
    // http://snipplr.com/view/58062/jquery-validation-additional-method-german-date/
    // http://stackoverflow.com/questions/511439/custom-date-format-with-jquery-validation-plugin
    // var $picker = $('.datepicker').pickadate({
    //     format: 'yy-mm-dd',
    //     formatSubmit: 'yy-mm-dd',
    //     onSelect: function () {
    //
    //         // Remove the delimiters
    //         var reformattedDate = this.getDate().replace(/-/g, '')
    //
    //         // Set the input value
    //         this.$node.val(reformattedDate)
    //
    //         // Set the hidden input value
    //         this.$node.siblings('input[type=hidden]').val(reformattedDate)
    //     }
    // })

});


