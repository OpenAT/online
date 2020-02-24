
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// function throttle(fn, threshhold, scope) {
//   threshhold || (threshhold = 250);
//   var last,
//       deferTimer;
//   return function () {
//     var context = scope || this;
//
//     var now = +new Date,
//         args = arguments;
//     if (last && now < last + threshhold) {
//       // hold on to it
//       clearTimeout(deferTimer);
//       deferTimer = setTimeout(function () {
//         last = now;
//         fn.apply(context, args);
//       }, threshhold);
//     } else {
//       last = now;
//       fn.apply(context, args);
//     }
//   };
// }

// https://remysharp.com/2010/07/21/throttling-function-calls
// http://benalman.com/projects/jquery-throttle-debounce-plugin/
$('a').one('click', _.debounce( function (e) {
    console.log('CLICK');
    return true;
}, 3000, true));


