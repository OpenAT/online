# -*- coding: utf-8 -*-
# © 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antonio Espinosa <antonioea@antiun.com>
# © 2015 Javier Iniesta <javieria@antiun.com>
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from openerp import models, fields, api, _
from openerp import SUPERUSER_ID
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)


class MailMassMailingContact(models.Model):
    """
    The E-Mail is the only indicator to which res.partner (PersonEmail) a list contact belongs. Therefore it
    can not be allowed to change the email after list contact creation if linked to a partner (PersonEmail).

    Some Basic Rules to avoid hijacking of data:
      - 'email' of PersonEmail can not be changed (updated) after creation of a PersonEmail record
      - 'personemail_id' can not be changed (updated) after once linked to the list contact
        - The only exception to this rule are partner merges (Dublettenzusammenlegung)
      - list contact 'email' can not be changed after linked to a PersonEmail
      - 'personemail_id' will be auto-linked an can not be removed if once set
      - we do NOT transfer person related data from the list contact to the linked res.partner except for the 'email'
        if a portal-user (in 'base.group_portal') is logged in
      - If logged in the PersonEmail that will be created always belongs to the logged in
        res.partner if the logged in user is a portal-user
      - SECURITY: personemail_id can only be explicitly set by user in the group
                  "mass_mailing.access_mass_mailing_contact" at list contact creation
      - SECURITY: Allow the website public_user to subscribe e-mails!
                  TODO: Maybe a better rule would be to allow write to list contacts wherere the partner_id is
                        the same as the logged in user partner

    Open questions and Todos:

    TODO: If logged in:
      - TODO: Allow multiple subscriptions to mailing lists (with checkboxes)
      - TODO: Allow multiple OPT-OUT to maling lists (with checkboxes)
    TODO: These Rules may only apply for list contacts linked to a massmailing list of no type or of type "email" !!!
    TODO: The Mass Mailing list type and mass mailing contact approval should to be separate addons!!!
    """
    _inherit = 'mail.mass_mailing.contact'

    # ATTENTION: personemail_id can only be set by users in the 'mass_mailing.access_mass_mailing_contact' group!
    personemail_id = fields.Many2one(comodel_name='frst.personemail', string="Person Email (FRST)",
                                     domain=[('email', '!=', False)])

    # ATTENTION: partner_id is just like a related field (could be done by related field but did not work as expected)
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner',
                                 computed="_compute_partner_id", store=False,
                                 search="_search_partner_id",
                                 readonly=True)

    # Log additional subscriptions after the record was created
    renewed_subscription_log = fields.Text(string="Renewed Subscription Log", readonly=True)
    renewed_subscription_date = fields.Datetime(string="Renewed Subscription", readonly=True)

    _sql_constraints = [
        ('personemail_list_uniq', 'unique(personemail_id, list_id)',
         _('An other list contact with this PersonEmail exits already for this mailing list! '
           'A PersonEmail can only by used once per mailing list. '))
    ]

    @api.multi
    @api.depends('personemail_id')
    def _compute_partner_id(self):
        for r in self:
            r.partner_id = r.personemail_id.partner_id if r.personemail_id else False

    def _search_partner_id(self, operator, value):
        return [('personemail_id.partner_id', operator, value)]

    @api.constrains('personemail_id', 'email', 'list_id')
    def _post_update_check(self):
        for r in self:
            if r.personemail_id:
                if not r.partner_id:
                    raise ValidationError('PersonEmail is set but Partner is missing!')
                if r.personemail_id.partner_id.id != r.partner_id.id:
                    raise ValidationError('The Partner and the Partner from PersonEmail do not match!')
                if r.email and r.email.lower() != r.personemail_id.email.lower():
                    raise ValidationError('The email is not matching the already linked PartnerEmail!')
            if r.list_id.partner_mandatory:
                if not r.personemail_id:
                    raise ValidationError('PersonEmail must be set if Partner Mandatory is enabled for the list!')

    @api.multi
    def _pre_update_check(self, vals):
        """ We only allow an update to 'email' if no PersonEmail is linked yet"""
        if 'email' in vals:
            for r in self:
                new_email = vals.get('email')
                if r.personemail_id:
                    if not new_email or new_email.lower() != r.personemail_id.email.lower():
                        raise Warning(_("You can not update the email to '%s' for record %s because it is "
                                        "already linked to PersonEmail %s with email %s!"
                                        % (new_email, r.id, r.personemail_id.id, r.personemail_id.email)))

    @api.multi
    def new_partner_vals(self):
        self.ensure_one()
        partner_vals = {'email': self.email,
                        'firstname': self.firstname if self.firstname else False,
                        'lastname': self.lastname if self.lastname else self.email}
        return partner_vals

    @api.multi
    def append_renewed_subscription_log(self, log_text):
        now = fields.datetime.now()
        log = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT) + '\n'
        log += str(log_text) + '\n\n'
        for r in self:
            log = log + r.renewed_subscription_log if r.renewed_subscription_log else log
            r.write({'renewed_subscription_date': now, 'renewed_subscription_log': log})

    @api.multi
    def link_personemail(self, create_vals=None):
        create_vals = {} if create_vals is None else create_vals
        recordset_to_return = self.env['mail.mass_mailing.contact']
        for r in self:
            # ALWAYS LINK TO PERSONEMAIL IF 'partner_mandatory' is set for the list
            # ---------------------------------------------------------------------
            if r.list_id.partner_mandatory and not r.personemail_id:
                assert not r.partner_id, "partner_id can not be set if personemail_id is not set!"
                assert not create_vals.get('personemail_id'), "personemail_id can not be in create_vals"
                assert not create_vals.get('partner_id'), "partner_id can not be in create_vals"
                if create_vals.get('email'):
                    assert create_vals['email'].lower() == r.email.lower(), \
                        "email in create_vals must match email of list contact"
                if create_vals.get('list_id'):
                    assert create_vals['list_id'] == r.list_id.id, \
                        "list_id in create_vals must match list_id of list contact"

                # Check if a Website-User is logged in
                # HINT: field 'share' on res.users is a computed field and will be set if the user is not in
                #       the 'base.group_user' group (see odoo/addons/share/res_users.py). So basically this means
                #       that we can see every user that is not in 'base.group_user' as an external user.
                user = self.env.user
                public_website_user_id = self.sudo().env.ref('base.public_user', raise_if_not_found=True).id
                if user.id not in (SUPERUSER_ID, public_website_user_id) and not user.has_group('base.group_user'):
                    websiteuser_partner = user.partner_id
                else:
                    websiteuser_partner = None

                # Case insensitive search domain for PartnerEmail
                pe_domain = [('email', '=ilike', r.email)]

                # Only search for PersonEmail records of the website-user
                if websiteuser_partner:
                    pe_domain += [('partner_id', '=', websiteuser_partner.id)]

                # Search case insensitive for PersonEmails with the email of this list contact
                pe_records = self.env['frst.personemail'].sudo().search(pe_domain)

                # All matching non-subscribed PersonEmail records
                # ATTENTION: !!! .filtered would honor the domain on the field definition !!!
                pe_free = pe_records.filtered(
                    lambda pe: r.list_id.id not in pe.mapped('mass_mailing_contact_ids.list_id').ids
                )

                # All matching subscribed PersonEmail records
                pe_subscribed = pe_records - pe_free

                # Update existing subscriptions
                # -----------------------------
                if pe_subscribed:
                    # Get the subscriptions
                    lc_subscribed = pe_subscribed.mapped('mass_mailing_contact_ids')

                    if create_vals:

                        # Update records if a user is logged in
                        if websiteuser_partner:
                            lc_subscribed.write(create_vals)

                        # Only update the renewed subscription fields for public users
                        else:
                            lc_subscribed.append_renewed_subscription_log(create_vals)

                    # Stop here if no non subscribed PartnerEmails where found
                    if not pe_free:
                        recordset_to_return = recordset_to_return | lc_subscribed
                        r.sudo().unlink()
                        continue

                # Create new subscriptions for existing PersonEmail(s)
                # -------------------------------------------------------
                if pe_free:
                    # Link current list contact to first non linked PersonEmail
                    pe_free_first = pe_free[0]
                    r.write({'personemail_id': pe_free_first.id})
                    recordset_to_return = recordset_to_return | r

                    # Avoid mail.thread auto subscription for the public-website-user
                    # TODO: Maybe this is inconsistent because we do not suppress mail.thread for pe_free_first
                    lc_obj_sudo = self.env['mail.mass_mailing.contact'].sudo()
                    if user.id == public_website_user_id:
                        lc_obj_sudo = lc_obj_sudo.with_context(mail_create_nolog=True)

                    # Create list contacts for all remaining non linked PersonEmails
                    for pe in pe_free - pe_free_first:

                        # Prepare values
                        lc_vals = create_vals.copy()
                        lc_vals['email'] = r.email
                        lc_vals['list_id'] = r.list_id.id
                        lc_vals['personemail_id'] = pe.id

                        # Create new list contact
                        lc_new = lc_obj_sudo.create(lc_vals)

                        # Add the record to the recordset that will be returned
                        recordset_to_return = recordset_to_return | lc_new

                    # Move on to the next list contact record
                    continue

                # Create a new subscription for a new PersonEmail
                # -----------------------------------------------
                # a) Create a new PersonEmail for the existing logged-in Person and link it to the current record
                # ATTENTION: We do not change the main email to avoid an email move!
                if websiteuser_partner:
                    last_email_update = fields.datetime.now()

                    # Make sure the new PersonEmail is not the new main email
                    if websiteuser_partner.main_personemail_id:
                        current_leu = websiteuser_partner.main_personemail_id.last_email_update
                        current_leu_dt = fields.datetime.strptime(current_leu, DEFAULT_SERVER_DATETIME_FORMAT)
                        last_email_update = current_leu_dt - timedelta(days=1)

                    # Create a new personemail which is not the new main email
                    pe = self.env['frst.personemail'].sudo().create(
                        {'email': r.email,
                         'partner_id': websiteuser_partner.id,
                         'last_email_update': last_email_update})

                    # Update the list contact record
                    r.write({'personemail_id': pe.id})

                    # Add the record to the recordset that will be returned
                    recordset_to_return = recordset_to_return | r

                    # Move on to the next list contact record
                    continue

                # b) Create a new PersonEmail and a new Person and link it to the current record
                else:
                    # Get the values for the new partner
                    partner_vals = r.new_partner_vals()

                    # Avoid mail.thread auto subscription for the public-website-user
                    partner_obj_sudo = self.env['res.partner'].sudo()
                    if user.id == public_website_user_id:
                        partner_obj_sudo = partner_obj_sudo.with_context(mail_create_nolog=True)

                    # Create the new partner and related PersonEmail
                    partner = partner_obj_sudo.create(partner_vals)

                    # Make sure the main PersonEmail matches the list contact email
                    assert partner.main_personemail_id.email.lower() == r.email.lower(), _(
                        "Emails (%s, %s) do not match after partner creation!"
                        "" % (partner.main_personemail_id.email, r.email))

                    # Update the list contact record
                    r.write({'personemail_id': partner.main_personemail_id.id})

                    # Add the record to the recordset that will be returned
                    recordset_to_return = recordset_to_return | r

                    # Move on to the next list contact record
                    continue

        return recordset_to_return

    @api.model
    def create(self, vals):
        # Avoid mail.thread auto subscription for website-users since they have no access to mail.message
        if not self.env.user.has_group('base.group_user'):
            self = self.with_context(mail_create_nolog=True)

        # Create the new record
        res = super(MailMassMailingContact, self).create(vals)

        # Link PersonEmail
        # HINT: Executes only if not already linked
        res_pe = None
        if res:
            res_pe = res.link_personemail(create_vals=vals)

        # In case we deleted the record we use one of the remaining records
        if not res.exists() and res_pe:
            res = res_pe[0]

        # Check if everything is ok
        #res._post_update_check()

        return res

    @api.multi
    def write(self, vals):
        # Make sure no email change is happening if already linked to PersonEmail
        self._pre_update_check(vals)

        # Update the records
        res = super(MailMassMailingContact, self).write(vals)

        # Link PersonEmail
        # HINT: Executes only if not already linked
        self.link_personemail()

        # Check if everything is ok
        #self._post_update_check()

        return res
