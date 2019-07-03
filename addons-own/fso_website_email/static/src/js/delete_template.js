(function () {
    'use strict';
    console.log('delete template')

    console.log(openerp.qweb)

    var templates = document.getElementsByClassName('fso_wem_delete_template');
    console.log(templates)

    for (var i = 0; i < templates.length; i++) {
        console.log(templates[i].id)
        templates[i].addEventListener("click", try_delete_template);
    }

    function try_delete_template (e) {
        console.log('clicked')
        console.log(e.path[0].id)
        var template_id = e.path[0].id;
        console.log(template_id)

        $('#email_templates').after(
            openerp.qweb.render(
                'fso_wem_delete', {template_id: template_id}
            ));

        var warning = document.getElementById('fso_wem_delete_modal');
        warning.style.display = 'block';

        var cancelButton = document.getElementsByClassName('close_fso_wem_modal');
        console.log(cancelButton)
        for (var i = 0; i < cancelButton.length; i++) {
            console.log(cancelButton[i].id)
            cancelButton[i].addEventListener("click", cancel_delete);
        }
    }

    function cancel_delete () {
        console.log('cancale')
        var toClose = document.getElementById('fso_wem_delete_modal');
        toClose.style.display = "none";
        $('#fso_wem_delete_modal').remove();
    }

})();