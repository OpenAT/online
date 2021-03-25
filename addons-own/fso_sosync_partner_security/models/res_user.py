# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api

import logging
logger = logging.getLogger(__name__)


class ResUserFRSTSecurity(models.Model):
    _inherit = "res.users"

    @api.model
    def create(self, vals):
        res = super(ResUserFRSTSecurity, self).create(vals)
        if res and res.partner_id:
            res.partner_id.compute_security_fields()
        return res

    @api.multi
    def write(self, vals):
        boolean_res = super(ResUserFRSTSecurity, self).write(vals)
        partner = self.mapped('partner_id')
        if partner:
            partner.compute_security_fields()
        return boolean_res
