/**
 * Created by mkarrer on 10.07.17.
 */

// https://github.com/ibericode/mailchimp-for-wordpress/issues/166
// Since bots will normally not click a button but just send the form this may prevent
// accidental auto form completion of honey pot fields from browsers
$(document).ready(function(){
  $('.btn').on('click',function(){
    $('.no-auto-comp').val('');
  });
});
