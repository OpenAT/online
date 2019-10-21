# -*- coding: utf-8 -*-
# © 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antonio Espinosa <antonioea@antiun.com>
# © 2015 Javier Iniesta <javieria@antiun.com>
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class MailMassMailingContact(models.Model):
    _inherit = 'mail.mass_mailing.contact'

    personemail_id = fields.Many2one(comodel_name='frst.personemail', string="Person Email (FRST)",
                                     domain=[('email', '!=', False)], readonly=True)
    #partner_id = fields.Many2one(related='personemail_id.partner_id', store=True)
    # Related field did not work for updates - therefore i try it now as a regular field
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner', readonly=True)

    _sql_constraints = [
        ('personemail_list_uniq', 'unique(personemail_id, list_id)',
         _('PersonEmail already exists in this mailing list.'))
    ]

    @api.constrains
    def _contraint_partner_id(self):
        for r in self:
            if r.personemail_id:
                if not r.partner_id:
                    raise ValidationError('PersonEmail is set but Partner is missing!')
                if r.personemail_id.partner_id.id != r.partner_id.id:
                    raise ValidationError('The Partner and the Partner from PersonEmail do not match!')

    @api.model
    def _get_personemail_id_partner_vals(self, vals, mailing_list):
        # Self must be a single record or empty.
        assert len(self) <= 1, _("The recordset must be empty or contain a single record only!")

        partner_vals = {}

        # Append the partner category tags from the mass mailing list
        if mailing_list.partner_category:
            partner_vals['category_id'] = [(4, mailing_list.partner_category.id, 0)]

        # Transfer additional fields to the partner
        partner_vals['email'] = vals.get('email', self.email if len(self) == 1 else False)
        partner_vals['name'] = vals.get('name', self.name if len(self) == 1 else False)

        # Fallback to the email for partner name if no 'name' was given for the list contact
        if not partner_vals['name']:
            partner_vals['name'] = partner_vals['email']

        # Make sure mandatory fields are all available
        if not partner_vals['email']:
            return {}

        return partner_vals

    @api.model
    def _get_personemail_id(self, vals):
        # TODO: If a user is already logged-in we should always create PersonEmail for the logged in user on e-mail
        #       changes - OR we do not allow the user to set a new email address but show it to him read-only in the
        #       form? DISCUSS IN TEAM

        # If personemail_id is already in vals (and therefore forced) we do NOT change it!
        if vals.get('personemail_id'):

            # Check that contact list email and personemail.email still match
            if vals.get('email'):
                vals_email = vals.get('email').strip().lower()
                personemail = self.env['frst.personemail'].sudo().browser([vals.get('personemail_id')])
                personemail_email = personemail.strip().lower()
                assert personemail_email == vals_email, _("PersonEmail is forced but does not match new email (%s, %s)"
                                                          "" % (personemail_email, vals_email))
            return vals['personemail_id']

        # Self must be a single record or empty.
        assert len(self) <= 1, _("The recordset must be empty or contain a single record only!")

        # Get the e-mail string and the mailing list id
        email = vals.get('email', self.email if len(self) == 1 else False)
        mailing_list_id = vals.get('list_id', self.list_id.id if len(self) == 1 else False)

        # Return without changes if no email to match the partner is available
        if not email or not mailing_list_id:
            return None

        # Search case insensitive for PersonEmail records with this e-mail
        personemail_records = self.env['frst.personemail'].sudo().search([('email', '=ilike', email.strip())], limit=2)

        # Link PersonEmail if exactly one was found
        if personemail_records and len(personemail_records) == 1:
            personemail_id = personemail_records[0].id
        # Create a new res.partner and therefore a new PartnerEmail if partner_mandatory is set
        # or return 'False' if partner_mandatory is not set
        else:
            mailing_list = self.env['mail.mass_mailing.list'].sudo().browse(mailing_list_id)
            if mailing_list.partner_mandatory:

                # Create res.partner
                partner_vals = self._get_personemail_id_partner_vals(vals, mailing_list)
                partner = self.env['res.partner'].sudo().create(partner_vals)
                partner_main_email = partner.main_personemail_id.email.strip().lower()

                # Check if the new main email of the partner is the one we just used
                # HINT: This is a safety net in case something unexpected changed in fso_frst_personemail
                if partner_main_email.strip().lower() != email.strip().lower():
                    raise AssertionError(_("Emails (%s, %s) do not match after partner creation!"
                                           % (email, partner_main_email)))

                # Use the id of the new main email
                personemail_id = partner.main_personemail_id.id

            else:

                # Do not link any PersonEmail
                personemail_id = False

        return personemail_id

    @api.model
    def _get_partner_id(self, vals):
        # Self must be a single record or empty.
        assert len(self) <= 1, _("The recordset must be empty or contain a single record only!")

        # Get the id of the personemail record
        personemail_id = vals.get('personemail_id', self.personemail_id.id if len(self) == 1 else False)

        if personemail_id:
            partner_id = self.env['frst.personemail'].sudo().browse([personemail_id]).partner_id.id
        else:
            partner_id = False

        return partner_id

    @api.model
    def create(self, vals):
        # Always try to link a PersonEmail on create if False or not in vals:
        vals['personemail_id'] = self._get_personemail_id(vals)
        # Always set the res.partner based on the personemail_id just like a related field!
        vals['partner_id'] = self._get_partner_id(vals)
        return super(MailMassMailingContact, self).create(vals)

    @api.multi
    def write(self, vals):
        # HINT: The E-Mail should basically not change for list contacts but if it changes we need to relink
        #       personemail_id also.
        if 'email' in vals:
            vals['personemail_id'] = self._get_personemail_id(vals)
        # Always set the res.partner based on the personemail_id just like a related field!
        vals['partner_id'] = self._get_partner_id(vals)
        return super(MailMassMailingContact, self).write(vals)
