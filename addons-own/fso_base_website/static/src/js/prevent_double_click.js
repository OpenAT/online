// prevent rappid clicks
// http://stackoverflow.com/questions/30883651/detach-and-reattach-event-listeners
// https://jsfiddle.net/UziTech/176fzorn
// http://stackoverflow.com/questions/4742610/attaching-jquery-event-handlers-so-that-they-are-triggered-first
// $(document).on("click", 'a', function(event) {
//     // Declare and trigger a "before-click" event.
//     $(this).trigger('before-click');
//
//     // Subsequent code run after the "before-click" events.
//
// }).on('before-click', function() {
//         // Run before the main body of the click event.
//         if($(this).data('lastClick') + 1600 > new Date().getTime()){
//             console.log('INVALID SECOND CLICK: do nothing');
//             event.preventDefault();
//             event.stopPropagation();
//             return false;
//         }
//
//         // First click
//         console.log('FIRST CLICK');
//         $(this).data('lastClick', new Date().getTime());
//         //return true;
//     });


// http://stackoverflow.com/questions/17249125/event-capturing-jquery
// $.fn.priorityOn = function (type, selector, data, fn) {
//     this.each(function () {
//         var $this = $(this);
//
//         var types = type.split(" ");
//
//         for (var t in types) {
//             $this.on(types[t], selector, data, fn);
//
//             var currentBindings = $._data(this, 'events')[types[t]];
//             if ($.isArray(currentBindings)) {
//                 currentBindings.unshift(currentBindings.pop());
//             }
//         }
//
//
//     });
//     return this;
// };
//
// $(document).priorityOn("click", 'a', '',function (e) {
//
//         // Avoid subsequent clicks
//         if($(this).data('lastClick') + 3000 > new Date().getTime()){
//             console.log('INVALID SECOND CLICK: do nothing');
//             e.stopImmediatePropagation();
//             e.preventDefault();
//             e.stopPropagation();
//             return false;
//         }
//         if($(this).data('lastClick') + 3000 < new Date().getTime()){
//             console.log('VALID SECOND CLICK: do nothing');
//             $(this).attr("disabled", false);
//             $(this).removeData('lastClick');
//             $(this).removeProp('lastClick');
//             return true;
//         }
//
//         // First click
//         console.log('FIRST CLICK: disable link');
//         $(this).data('lastClick', new Date().getTime());
//         $(this).attr("disabled", true);
//         //return true;
// });
