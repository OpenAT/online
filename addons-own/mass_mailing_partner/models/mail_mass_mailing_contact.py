# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)


class MailMassMailingContact(models.Model):
    """
    Link mass mailing contact records to frst.personemail records if partner_mandatory is set on the mailing list
    """
    _inherit = 'mail.mass_mailing.contact'

    # ATTENTION: personemail_id can only be set by users in the 'mass_mailing.access_mass_mailing_contact' group!
    personemail_id = fields.Many2one(comodel_name='frst.personemail', string="Person Email (FRST)",
                                     domain=[('email', '!=', False)])

    # ATTENTION: This is not available in Fundraising Studio!
    pe_partner_id = fields.Many2one(string="Partner der PersonEmail", comodel_name='res.partner',
                                    related="personemail_id.partner_id", store=True, readonly=True,
                                    help="Shows the partner of the linked PersonEmail. It's only for convenience!")

    # Log additional subscriptions after the record was created
    # HINT: This is needed since we can not always use the chatter because the partner of the user may not have
    #       an email address or the partner belongs to the public group which has no mail.thread access at all
    renewed_subscription_log = fields.Text(string="Renewed Subscription Log", readonly=True)
    renewed_subscription_date = fields.Datetime(string="Renewed Subscription", readonly=True)

    # --------------------------
    # CONSTRAINS AND VALIDATIONS
    # --------------------------
    # Make sure a PersonEmail can only be subscribed once per mail.mass_mailing.list
    _sql_constraints = [
        ('personemail_list_uniq', 'unique(personemail_id, list_id)',
         _('An other list contact with this PersonEmail exits already for this mailing list! '
           'A PersonEmail can only by used once per mailing list. '))
    ]

    @api.multi
    def _pre_update_check(self, vals):
        """ We only allow an update to 'email' if no PersonEmail is linked yet"""
        if 'email' in vals:
            for r in self.sudo():
                new_email = vals.get('email')
                if r.personemail_id:
                    if not new_email or new_email.lower() != r.personemail_id.email.lower():
                        raise Warning(_("You can not update the email to '%s' for record %s because it is "
                                        "already linked to PersonEmail %s with email %s!"
                                        % (new_email, r.id, r.personemail_id.id, r.personemail_id.email)))

    @api.multi
    def _post_update_check(self):
        for r in self.sudo():
            if r.personemail_id:
                if r.email and r.email.lower() != r.personemail_id.email.lower():
                    raise ValidationError(_('The email is not matching the linked PartnerEmail!'))
            if r.list_id.partner_mandatory:
                if not r.personemail_id:
                    raise ValidationError(_('PersonEmail must be set if Partner Mandatory is enabled for the list!'))

    # ------
    # HELPER
    # ------
    @api.model
    def _is_logged_in(self):
        # The default website user does not count as a logged in user
        default_website_user = self.sudo().env.ref('base.public_user', raise_if_not_found=False)
        if not self.env.user or (default_website_user and default_website_user.id == self.env.user.id):
            return False
        return True

    @api.model
    def _is_public_user(self):
        if self.env.user.has_group('base.group_user'):
            return False
        if self._is_logged_in() and self.env.user.has_group('base.group_public'):
            return True
        return False

    @api.multi
    def append_renewed_subscription_log(self, log_text):
        now = fields.datetime.now()
        log = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT) + '\n'
        log += str(log_text) + '\n\n'
        for r in self:
            log = log + r.renewed_subscription_log if r.renewed_subscription_log else log
            r.write({'renewed_subscription_date': now, 'renewed_subscription_log': log})

    # ----------------------
    # COMPUTE PERSONEMAIL V2
    # ----------------------
    @api.model
    def _get_existing_list_contact(self, list_id, email):
        assert int(list_id), "list_id not given or no integer"

        # Search for an existing mass mailing list contact as superuser
        existing_list_contact = self.sudo().search([
            ('list_id', '=', list_id),
            ('email', '=ilike', email)
        ], limit=2, order='id')

        # Return the existing mail.mass_mailing.contact if exactly one record was found
        return existing_list_contact if len(existing_list_contact) == 1 else None

    @api.model
    def _get_existing_personemail(self, email):
        domain = [('email', '=ilike', email)]

        if self._is_public_user():
            domain += [('partner_id', '=', self.env.user.partner_id.id)]

        # Search for an existing frst.personemail as superuser
        existing = self.env['frst.personemail'].sudo().search(domain, limit=2, order='id')

        # Return the existing frst.personemail if exactly one record was found
        return existing if len(existing) == 1 else None

    @api.model
    def new_personemail_vals(self, email, partner, list_contact_vals=None, replace_main_email=False):
        personemail_vals = {
            'email': email,
            'partner_id': partner.id,
        }
        if not replace_main_email and partner.main_personemail_id and partner.main_personemail_id.last_email_update:
            me_last_update = fields.datetime.strptime(partner.main_personemail_id.last_email_update,
                                                      DEFAULT_SERVER_DATETIME_FORMAT)
            personemail_vals['last_email_update'] = me_last_update - timedelta(days=1)
        return personemail_vals

    @api.model
    def new_partner_vals(self, list_contact_vals):
        partner_vals = {'email': list_contact_vals['email'],
                        'firstname': list_contact_vals.get('firstname', False),
                        'lastname': list_contact_vals.get('lastname', False)}
        return partner_vals

    @api.model
    def get_personemail(self, list_contact_vals):
        email = list_contact_vals['email']

        # Search for an existing personemail that we can use
        person_email = self._get_existing_personemail(email=email)

        if not person_email:

            # CREATE A NEW FRST.PERSONEMAIL (for the logged in public user partner as the superuser)
            # HINT: Do not replace the current main personemail with the new personemail! (last_email_update)
            if self._is_public_user():
                personemail_vals = self.new_personemail_vals(email=email,
                                                             partner=self.env.user.partner_id,
                                                             list_contact_vals=list_contact_vals,
                                                             replace_main_email=False)
                person_email = self.env['frst.personemail'].sudo().create(personemail_vals)

            # CREATE A NEW RES.PARTNER (and therefore a new frst.personemail as the superuser)
            else:
                partner_vals = self.new_partner_vals(list_contact_vals)
                new_partner = self.env['res.partner'].sudo().create(partner_vals)
                person_email = new_partner.main_personemail_id

        assert len(person_email) == 1, _("Mandatory frst.personemail was not created for new res.partner created "
                                         "with email set!")
        return person_email

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, vals):
        # Avoid mail.thread auto subscription for website-users since they have no access to mail.message and
        # for all other user where the res.partner of the user has no email
        if not self.env.user.has_group('base.group_user') or not self.env.user.partner_id.email:
            self = self.with_context(mail_create_nolog=True)

        mailing_list = self.env['mail.mass_mailing.list'].sudo().browse(vals['list_id'])
        email = vals['email']

        if mailing_list.partner_mandatory:
            # Update and return an existing mail.mass_mailing.contact
            existing_contact = self._get_existing_list_contact(list_id=mailing_list.id, email=email)
            if existing_contact:
                existing_contact.append_renewed_subscription_log(vals)
                if self._is_logged_in():
                    existing_contact.write(vals)
                existing_contact._post_update_check()
                return existing_contact

            # Link a frst.personemail to the mail.mass_mailing.contact (append pe id to create values)
            else:
                if not vals.get('personemail_id'):
                    personemail = self.get_personemail(list_contact_vals=vals)
                    vals['personemail_id'] = personemail.id

        record = super(MailMassMailingContact, self).create(vals)
        record._post_update_check()
        return record

    @api.multi
    def write(self, vals):
        self._pre_update_check(vals=vals)

        # Update the record(s)
        boolean_result = super(MailMassMailingContact, self).write(vals)

        self._post_update_check()

        return boolean_result
