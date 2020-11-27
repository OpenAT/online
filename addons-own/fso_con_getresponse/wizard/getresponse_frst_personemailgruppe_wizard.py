# -*- coding: utf-8 -*-
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class GetresponseFRSTPersonemailgruppeWizard(models.TransientModel):
    _name = "getresponse.frst.personemailgruppe.wizard"

    # DEFAULTS
    def compute_contact_binding_ids(self):
        bindings = self.env['getresponse.frst.personemailgruppe'].browse(self._context.get('active_ids'))
        if bindings:
            self.contact_binding_ids = bindings

    def _default_contact_binding_ids(self):
        bindings = self.env['getresponse.frst.personemailgruppe'].browse(self._context.get('active_ids'))
        return bindings

    # FIELDS
    contact_binding_ids = fields.Many2many('getresponse.frst.personemailgruppe',
                                           string="Contact Bindings",
                                           compute="compute_contact_binding_ids",
                                           default=_default_contact_binding_ids)

    # METHODS
    @api.multi
    def wizard_export_contact_bindings_delayed(self):
        _logger.info("Create export jobs for %s getresponse.frst.personemailgruppe bindings by wizard!"
                     "" % len(self.contact_binding_ids))
        self.contact_binding_ids.export_getresponse_contact_delay()

    @api.multi
    def wizard_import_contact_bindings_delayed(self):
        _logger.info("Create import jobs for %s getresponse.frst.personemailgruppe bindings by wizard!"
                     "" % len(self.contact_binding_ids))
        self.contact_binding_ids.import_getresponse_contact_delay()
