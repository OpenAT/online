/* 
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

// // Custom show and hide events for jquery .on()
// // http://viralpatel.net/blogs/jquery-trigger-custom-event-show-hide-element/
// (function ($) {
//     $.each(['show', 'hide'], function (i, ev) {
//         var el = $.fn[ev];
//         $.fn[ev] = function () {
//             this.trigger(ev);
//             return el.apply(this, arguments);
//         };
//     });
// })(jQuery);
//
// // Custom Modal Colors
// //
// $('.modal[data-color]').on('show hide', function () {
//     // console.log("Modal Box with data-color visibility changed");
//     $('.modal-backdrop').toggleClass('modal-backdrop-' + $(this).data('color'));
// });

// // http://stackoverflow.com/questions/10585689/change-the-background-color-in-a-twitter-bootstrap-modal
// $('#popupbox').data('bs.modal').$backdrop.css('background-color','orange')

// Show PopUpBox at Page Load and add custom class for custom background
$(document).ready(function () {
    $('#popupbox').modal('show');
    $('.modal-backdrop').addClass('modal-backdrop-popupbox');
});
