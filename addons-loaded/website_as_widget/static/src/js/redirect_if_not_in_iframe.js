$( 'meta[name=aswidget-redirect-url]' ).ready(function () {

    // Check if a redirection URL exists
    var aswidget_redirect_url = $( 'meta[name=aswidget-redirect-url]' ).attr('content');
    // Redirect if we are not in an (i) frame
    if ( aswidget_redirect_url && window.self == window.top ) {
        window.location.replace(aswidget_redirect_url);
    };

});
