# -*- coding: utf-8 -*-
# © 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antonio Espinosa <antonioea@antiun.com>
# © 2015 Javier Iniesta <javieria@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class MailMassMailingList(models.Model):
    _inherit = 'mail.mass_mailing.list'

    partner_mandatory = fields.Boolean(string="Mandatory Partner",
                                       default=False)
    partner_category = fields.Many2one(comodel_name='res.partner.category',
                                       index=True,
                                       string="Partner Tag")

    @api.constrains('partner_mandatory')
    def constrain_partner_mandatory(self):
        for mlist in self.sudo():
            if mlist.partner_mandatory:
                if mlist.env['mail.mass_mailing.contact'].search([('list_id', '=', mlist.id),
                                                                  ('personemail_id', '=', False)],
                                                                 limit=1, order='id'):
                    raise ValidationError(_("partner_mandatory is set but one or more list contacts are not linked to "
                                            "a personemail!"))
