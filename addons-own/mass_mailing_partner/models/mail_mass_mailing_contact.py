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
    TODO: These Rules may only apply for list contacts linked to a massmailing list of "no-type" or of type "email" !!!
    TODO: The Mass Mailing list type and mass mailing contact approval should to be separate addons!!!
    """
    _inherit = 'mail.mass_mailing.contact'

    # ATTENTION: personemail_id can only be set by users in the 'mass_mailing.access_mass_mailing_contact' group!
    personemail_id = fields.Many2one(comodel_name='frst.personemail', string="Person Email (FRST)",
                                     domain=[('email', '!=', False)])

    # ATTENTION: This is not available in Fundrasing Studio!
    pe_partner_id = fields.Many2one(string="Partner der PersonEmail", comodel_name='res.partner',
                                    related="personemail_id.partner_id", store=True, readonly=True,
                                    help="Shows the partner of the linked PersonEmail. It's only for convenience!")

    # Log additional subscriptions after the record was created
    renewed_subscription_log = fields.Text(string="Renewed Subscription Log", readonly=True)
    renewed_subscription_date = fields.Datetime(string="Renewed Subscription", readonly=True)

    # Make sure a PersonEmail can only be subscribed once per mail.mass_mailing.list
    _sql_constraints = [
        ('personemail_list_uniq', 'unique(personemail_id, list_id)',
         _('An other list contact with this PersonEmail exits already for this mailing list! '
           'A PersonEmail can only by used once per mailing list. '))
    ]

    @api.multi
    def _post_update_check(self):
        for r in self:
            if r.personemail_id:
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
    def _update_existing_contact_on_create(self, vals):
        self.ensure_one()

        # Skipp if partner_mandatory is not set on the mass mailing list
        if not self.list_id.partner_mandatory:
            _logger.info("Skipp _renew_subscription_on_create() for mass mailing contact (id %s) because "
                         "partner_mandatory is not enabled for mass mailing list (id %s)" % (self.id, self.list_id.id))
            return None

        # Search for an existing list contact
        existing = self.search([
            ('list_id', '=', self.list_id.id),
            ('email', '=', self.email)
        ], limit=2, order='id')

        # Skipp if none or more than one list contact is found
        if len(existing) != 1:
            if len(existing) > 1:
                _logger.error("Skipp _renew_subscription_on_create() for mass mailing contact (id %s) because %s "
                              "records where found in mass mailing list (id %s) for email %s"
                              "" % (self.id, len(existing), self.list_id.id, self.email))
            return None

        # Check if a user is logged in
        user = self.env.user
        default_website_user = self.sudo().env.ref('base.public_user', raise_if_not_found=True)

        # Update existing record values if a user is logged in
        if user.id != default_website_user.id:
            existing.write(vals)

        # Only update the renew log fields if no user is logged in
        else:
            existing.append_renewed_subscription_log(vals)

        # Delete the created (but not yet committed-to-db) list contact
        self.unlink()

        # Return the updated list contact
        return existing

    @api.multi
    def compute_personemail_id(self):
        """ Link the mass mailing contact to a Fundraising Studio PersonEmail and it's related res.partner if
        partner_mandatory is enabled on the mass mailing list.
        """
        for r in self:
            # Skipp if already linked to a PersonEmail
            if r.personemail_id:
                _logger.info("Skipp compute_personemail_id() because mass mailing contact (id %s) is already linked to"
                             " a frst.personemail (id %s)" % (r.id, r.personemail_id.id))
                continue

            # Skipp if partner_mandatory is not set on the mass mailing list
            if not r.list_id.partner_mandatory:
                _logger.info("Skipp compute_personemail_id() for mass mailing contact (id %s) because partner_mandatory"
                             " is not enabled for mass mailing list (id %s)" % (r.id, r.list_id.id))
                continue

            # E-Mail search domain
            # HINT: '=ilike' case insensitive exact search
            domain = [('email', '=ilike', r.email)]

            # Limit search domain for logged-in non-regular-users (portal/public users)
            user = self.env.user
            default_website_user = self.sudo().env.ref('base.public_user', raise_if_not_found=True)
            logged_in_partner = None
            if user.id not in (SUPERUSER_ID, default_website_user.id) and not user.has_group('base.group_user'):
                logged_in_partner = user.partner_id
                domain += [('partner_id', '=', user.partner_id.id)]

            # Search for existing frst.personemail with the same email than the list contact
            person_emails = self.env['frst.personemail'].sudo().search(domain, limit=2)

            p_email_to_set = None

            # A) USE EXITING-PERSON-EMAIL IF EXACTLY ONE WAS FOUND WITH NO LINKED LIST CONTACTS FOR THIS LIST
            if len(person_emails) == 1:
                if all(p_email_lc.list_id.id != r.list_id.id for p_email_lc in person_emails.mass_mailing_contact_ids):
                    p_email_to_set = person_emails

            # B) CREATE A NEW PERSON EMAIL FOR THE PARTNER OF THE LOGGED IN USER
            if not p_email_to_set and logged_in_partner:
                new_pe_vals = {'email': r.email,
                               'partner_id': logged_in_partner.id}

                # Do not replace the current main e-mail of a logged in partner (create an "older" personemail)
                if logged_in_partner.main_personemail_id:
                    if logged_in_partner.main_personemail_id.last_email_update:
                        main_email_leu = logged_in_partner.main_personemail_id.last_email_update
                        main_email_leu = fields.datetime.strptime(main_email_leu, DEFAULT_SERVER_DATETIME_FORMAT)
                        new_pe_vals['last_email_update'] = main_email_leu - timedelta(days=1)

                p_email_to_set = self.env['frst.personemail'].sudo().create(new_pe_vals)

            # C) CREATE A NEW PARTNER WITH A NEW PERSON EMAIL
            if not p_email_to_set:
                # Get the values for the new partner
                partner_vals = r.new_partner_vals()

                # Avoid mail.thread auto subscription for the public-website-user
                partner_obj_sudo = self.env['res.partner'].sudo().with_context(mail_create_nolog=True)

                # Create the new partner which will automatically create a new person email
                new_partner = partner_obj_sudo.create(partner_vals)

                # Make sure the main PersonEmail matches the list contact email
                if new_partner.main_personemail_id.email.lower() != r.email.lower():
                    raise ValueError("compute_personemail_id() for mass mailing contact (id %s) failed because ")

                p_email_to_set = new_partner.main_personemail_id

            # UPDATE LIST CONTACT WITH PERSONEMAIL_ID
            r.write({'personemail_id': p_email_to_set.id})

    @api.model
    def create(self, vals):
        # Avoid mail.thread auto subscription for website-users since they have no access to mail.message
        if not self.env.user.has_group('base.group_user'):
            self = self.with_context(mail_create_nolog=True)

        # Create the new record
        res = super(MailMassMailingContact, self).create(vals)

        # Update existing list contact instead of creating a new one if partner mandatory is enabled
        # HINT: This will also unlink the 'res' record if an existing record to update is found!
        if res:
            existing = res._update_existing_contact_on_create(vals)
            if existing:
                return existing

        # Link PersonEmail if partner mandatory is enabled
        if res and not vals.get('personemail_id'):
            res.compute_personemail_id()

        self._post_update_check()

        return res

    @api.multi
    def write(self, vals):
        self._pre_update_check(vals=vals)

        # Update the records
        res = super(MailMassMailingContact, self).write(vals)

        # Link PersonEmail
        # HINT: Executes only if not already linked
        if res and not vals.get('personemail_id'):
            self.compute_personemail_id()

        self._post_update_check()

        return res
