$( document ).ready(function() {

    $("#get_text_from_html").on("click", function () {
        $("#fso_email_text").html($('#email_body_html').text())
    });

});
