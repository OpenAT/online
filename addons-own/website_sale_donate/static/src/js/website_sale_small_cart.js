$(document).ready(function () {
    // Remove product from (small) cart
    $(".oe_cart a.remove_product").click( function () {
        var data_line_id = $(this).data('line-id');
        console.log(data_line_id);
        var $small_cart_input = $(".oe_website_sale").find("input.js_quantity[data-line-id='"+data_line_id+"']");
        $small_cart_input.val( '0' );
        $small_cart_input.trigger( 'change' );
    });
});
