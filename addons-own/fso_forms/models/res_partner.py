# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerFsoForms(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    information_email_receipient_fso_form = fields.Many2one(comodel_name="fson.form",
                                                            inverse_name="information_email_receipients",
                                                            readonly=True, index=True, ondelete='set null')

