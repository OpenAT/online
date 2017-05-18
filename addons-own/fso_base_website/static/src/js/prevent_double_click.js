// prevent rappid clicks
// http://stackoverflow.com/questions/30883651/detach-and-reattach-event-listeners
// https://jsfiddle.net/UziTech/176fzorn
$(document).on("click", 'a', function(event) {

    if($(this).data('lastClick') + 1600 > new Date().getTime()){
        console.log('INVALID SECOND CLICK: do nothing');
        event.preventDefault();
        event.stopPropagation();
        return false;
    }

    // First click
    console.log('FIRST CLICK');
    $(this).data('lastClick', new Date().getTime());
    //return true;
});
