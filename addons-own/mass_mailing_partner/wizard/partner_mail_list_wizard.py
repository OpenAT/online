# -*- coding: utf-8 -*-
# © 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antonio Espinosa <antonioea@antiun.com>
# © 2015 Javier Iniesta <javieria@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields, _
from openerp.exceptions import Warning as UserError


# TODO: This wizard will not work currently because the field 'partner_id' was changed to an related field - must
#       be reworked!
class PartnerMailListWizard(models.TransientModel):
    _name = "partner.mail.list.wizard"
    _description = "Add multiple partners to one mailing list"

    mail_list_id = fields.Many2one(comodel_name="mail.mass_mailing.list",
                                   string="Mailing List")
    partner_ids = fields.Many2many(
        comodel_name="res.partner", relation="mail_list_wizard_partner",
        domain="[('email', '!=', False)]",
        default=lambda self: self.env.context.get("active_ids"))

    @api.multi
    def add_to_mail_list(self):
        contact_obj = self.env['mail.mass_mailing.contact']
        for partner in self.partner_ids:

            if not partner.email:
                raise UserError(_("Partner '%s' has no email.") % partner.name)


            contact_vals = {
                'partner_id': partner.id,
                'email': partner.email,
                'firstname': partner.firstname,
                'lastname': partner.lastname,
                'list_id': self.mail_list_id.id
            }

            contact_obj.create(contact_vals)
