$(document).ready(function () {

    // Remove product from cart and small cart
    $(".oe_cart a.remove_product").click( function () {
        var data_line_id = $(this).data('line-id');

        // Set the att_qty input also to zero for product pages (important for one-page-checkout templates)
        $(".js_add_cart_variants").find("input.js_quantity[data-line-id='"+data_line_id+"']").val( '0' );
        $(".js_add_cart_variants").find("input.js_quantity[data-line-id='"+data_line_id+"']").trigger( 'change' );

        // set the small_cart of cart input to 0 and trigger the change
        var $small_cart_input = $(".oe_cart").find("input.js_quantity[data-line-id='"+data_line_id+"']");
        $small_cart_input.val( '0' );
        $small_cart_input.trigger( 'change' );
    });
});
