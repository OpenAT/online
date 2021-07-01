# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    name_anonymized = fields.Char(string='Name Anonymized', compute="compute_name_anonymized")

    @api.depends('firstname', 'lastname')
    def compute_name_anonymized(self):
        for partner in self:
            if partner.firstname and partner.lastname and len(partner.lastname) > 4:
                partner.name_anonymized = "%s %s." % (partner.firstname, partner.lastname[:1])
            else:
                firstname = partner.firstname[:1] + '.' if partner.firstname else ''
                lastname = partner.lastname[:1] + '.' if partner.lastname else ''
                if firstname or lastname:
                    partner.name_anonymized = "%s %s" % (firstname, lastname)
                else:
                    partner.name_anonymized = _("Anonym.")
