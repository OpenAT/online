(function () {
    'use strict';

    var templates = document.getElementsByClassName('fso_wem_delete_template');

    for (var i = 0; i < templates.length; i++) {
        templates[i].addEventListener("click", try_delete_template);
    }

    function try_delete_template (e) {
        var template_id = e.path[0].dataset.templateId;

        $('#email_templates').after(
            openerp.qweb.render(
                'fso_wem_delete', {template_id: template_id}
            ));

        var warning = document.getElementById('fso_wem_delete_modal');
        warning.style.display = 'block';

        var cancelButton = document.getElementsByClassName('close_fso_wem_modal');
        for (var i = 0; i < cancelButton.length; i++) {
            cancelButton[i].addEventListener("click", cancel_delete);
        }
    }

    function cancel_delete () {
        var toClose = document.getElementById('fso_wem_delete_modal');
        toClose.style.display = "none";
        $('#fso_wem_delete_modal').remove();
    }

})();