$( document ).ready(function() {

    $('body').on('click', '#get_text_from_html', function () {
        if (confirm('Sicher? Der Text wird überschrieben!')) {

            function anotate_print_fields($element) {
                let print_fields = $element.find('.drop_in_print_field');
                print_fields
                    .each(function (pf_idx, pf) {
                        let $pf_current = $(pf)
                        $pf_current
                            .find("> span")
                            .each(function (pf_span_idx, pf_span) {
                                let $pf_span = $(pf_span)
                                if ($pf_span.css('display') !== 'none') {
                                    $pf_current.attr("data-fs-email-placeholder-active", $pf_span.attr("data-fs-email-placeholder"))
                                }
                            });
                    })
            }

            // Annotate the print fields with data-fs-email-placeholder-active
            anotate_print_fields($('#email_body_html'));

            // Copy the html to replace the print fields with its placeholder
            let $email_body_copy = $('#email_body_html').clone(deepWithDataAndEvents=true);
            $email_body_copy.find(".drop_in_print_field").each(function (idx, pf) {
                $pf = $(pf);
                $pf.replaceWith($pf.attr("data-fs-email-placeholder-active"));
            })

            // Remove the annotations
            $('#email_body_html *[data-fs-email-placeholder-active]').removeAttr("data-fs-email-placeholder-active");

            // Replace the content of #fso_email_text with the parsed text
            let fso_email_text = htmlToPlainText($email_body_copy.html());
            let fso_email_text_html = fso_email_text.replaceAll("\n", "<br>")

            $("#fso_email_text").html(fso_email_text_html);

        }
    })

});
