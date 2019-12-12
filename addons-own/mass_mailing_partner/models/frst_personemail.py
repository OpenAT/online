# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class FrstPersonEmail(models.Model):
    _inherit = 'frst.personemail'

    mass_mailing_contact_ids = fields.One2many(
        string="Mailing List Contacts",
        oldname="mass_mailing_contacts",
        comodel_name='mail.mass_mailing.contact', inverse_name='personemail_id')

    mass_mailing_stats = fields.One2many(
        string="Mass mailing stats",
        comodel_name='mail.mail.statistics', inverse_name='personemail_id')

    @api.constrains('email')
    def _constraint_mass_mailing_contact_ids(self):
        for r in self:
            if r.mass_mailing_contact_ids and not r.email:
                raise ValidationError(
                    _("This PartnerEmail '%s' is subscribed to one or more "
                      "mailing lists. Email must be assigned." % r.email))

    @api.multi
    def write(self, vals):
        res = super(FrstPersonEmail, self).write(vals)

        # TODO: Set Approval state of mass mailing contacts when the state of the PersonEmail Changes!

        return res
