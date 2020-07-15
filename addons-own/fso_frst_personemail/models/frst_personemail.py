# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.addons.fso_base.tools.validate import is_valid_email

from datetime import timedelta

import time
import logging
logger = logging.getLogger(__name__)


class FRSTPersonEmail(models.Model):
    """
    PersonEmail implements the Fundraising Studio Model of multiple E-Mails per person (res.partner).
    A PersonEmail can also belong to one or more zGruppeDetail which are considered as 'groups' in Fundraising Studio

    The relation of a zGruppeDetail to an PersonEmail is done by the model PersonEmailGruppe. This extra model was
    needed because in PersonEmailGruppe you could also define gueltig_von and gueltig_bis which tells if the
    zGruppeDetail is currently "active" (enabled) for the particular related PersonEmail (E-Mail Address)

    There is also a gueltig_von and gueltig_bis in zGruppeDetail but these Fields are considered as deprecated
    and should not be used anymore. They may even get deleted in the near future.

    Only one E-Mail address needed for a partner
    --------------------------------------------
    In a lot of circumstances we can only deal with one e-mail address per person (res.partner). E.g.: in face2face
    forms, website forms, interfaces with third party apps, ... only one e-mail address is used and send.

    If it is mandatory to only send/receive one e-mail address we choose the PersonEmail where the field email
    was updated last (indicated by the field last_email_update) and the email seems to contain a well formatted email
    address (indicated by the state 'active').

    To make it easier to see and select which e-mail is the actual main e-mail address we calculate the boolean field
    main_address. The e-mail address of the current main email-address if further set in the field email of res.partner.
    Vice versa if the field email of a partner is set or changed we will activate an existing PersonEmail by setting
    gueltig_von and gueltig_bis and updating last_email_update or create a new PersonEmail. This holds also true if we
    receive e-mail address updates from any other source e.g. from face2face forms or an website form.

    This means that the last valid e-mail address we get is always considered as the main e-mail address for a person.

    gueltig_von and gueltig_bis
    ---------------------------
    Since a PersonEmail is only active for a certain time range we must periodically check/set the state field of
    PersonEmail records based on gueltig_von and gueltig_bis. This is done every hour by a cron job.

    gueltig_von and gueltig_bis can be set in the GUI by users BUT be aware that if we receive (import) an email address
    by an external data source (web form, csv from face2face, ...) we may change gueltig_von and gueltig_bis to
    re-enable an existing PersonEmail!

    Todo: It is still do be discussed whether or not a user can completely delete/deactivate a PersonEmail if this
          e-mail is re-imported into Fundraising Studio from external sources. If so the 'active' field would be an
          obvious choice.

    user account login and e-mail addresses
    ---------------------------------------
    In most cases the e-mail address of a person will be used for the login field of the related res.user.
    If a person (res.partner) creates an account (res.user) automatically by a click on a token link or manually by
    registration on the website we would suggest or even force the login to be an email address or exactly the address
    in field 'email' of the related res.partner.

    If the email changes after the res.user was created the 'login' will not be changed automatically!

    Todo: How and when to change a 'login' of a res.user has to be discussed by the dev team in the near future!

    Thoughts about the future
    -------------------------
    Maybe PersonEmail should only be seen in the future as an "historical view" to email changes of a person

    E-Mail subscriptions would then be by person and not by e-mail. If a person changes or updates it's e-mail
    all E-Mail subscriptions would just go to the new email address after it's validation.

    This implies that on every e-mail change the person must validate that the person has access to the changed
    e-mail address before further e-mails can be send! As long as this validation is not done the last validated
    e-mail address would still be used as long as the new e-mail address is validated.
    """
    _name = "frst.personemail"
    _rec_name = "email"

    _inherit = ['fso.merge']

    email = fields.Char(string="E-Mail", required=True,
                        help="This field should normally NEVER change after record creation. The only exception"
                             "to this rule would be a quick typo fix after manual creation in FRST GUI.")
    last_email_update = fields.Datetime(string="Last Email Update", readonly=True,
                                        help="Basically this is the order/sequence of the PersonEmails of a Person. The"
                                             "latest PersonEmail with a valid e-mail address should normally be the "
                                             "current main email address.",
                                        index=True)

    # Partner related to this e-mail address
    partner_id = fields.Many2one(string="Person", required=True, ondelete='cascade',
                                 comodel_name="res.partner", inverse_name='frst_personemail_ids',
                                 help="This field should normally NEVER change after record creation. The only "
                                      "exception to this rule would be a quick typo fix after manual creation in FRST "
                                      "GUI.",
                                 index=True)
    partner_main_email_ids = fields.One2many(string="Main E-Mail Partner(s)",
                                             comodel_name='res.partner', inverse_name='main_personemail_id',
                                             readonly=True,
                                             help="The partner where this e-mail is the main E-Mail. Must be one "
                                                  "partner only and must match the partner_id field!")

    # create_date and deactivated_date
    gueltig_von = fields.Date(string="GültigVon", required=True,
                              default=lambda s: fields.datetime.now(),
                              help="This can be seen as the create_date in Fundraising Studio and is NOT "
                                   "supposed to change or be changed by the user!")
    gueltig_bis = fields.Date(string="GültigBis", required=True,
                              help="This can be seen as 'de-activated at' like if we would store the date when we set"
                                   "active to False in odoo. It is NOT supposed to disable the email address"
                                   "in the future!!! (Discussed with Rufus on 10.07.2018 by skype)",
                              default="2099-12-31")

    # State
    state = fields.Selection(string="State", readonly=True,
                             selection=[('active', 'Active'), ('inactive', 'Inactive')],
                             #compute="compute_state", store=True,
                             help="A PersonEmail has a state of active if the e-mail format seems valid and now is "
                                  "inside gueltig_von and gueltig_bis")

    # Main email address indicator (computed in CRUD)
    main_address = fields.Boolean(string="Main Address", readonly=True,
                                  # compute="compute_main_address", store=True,
                                  help="This indicates if the record is the primary active e-mail address. "
                                       "It will be used in webforms or exports where only one e-mail is allowed."
                                       "It should match with the email field in res.partner!")

    # Force an email to be the main_address
    forced_main_address = fields.Boolean(string="Forced Main Address",
                                         help="If set this Email will always be the main address! Can only be set"
                                              "if the address is in state active. If the forced main email becomes "
                                              "'inactive' it will not be the main email adress but the last changed"
                                              "personemail until it is reactivated again.")

    # E-Mail approval information
    # ATTENTION: If bestaetigt_am_um is set the E-Mail counts as approved!
    bestaetigt_am_um = fields.Datetime("Bestaetigt", readonly=True)
    bestaetigt_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn'),
                                                 ('manually', "Manually Approved"),
                                                 ],
                                        string="Bestaetigungs Typ", readonly=True)
    bestaetigt_herkunft = fields.Char("Bestaetigungsherkunft", readonly=True,
                                      help="E.g.: The link or the workflow process")

    # -------
    # METHODS
    # -------
    @api.multi
    def get_forced(self):
        """ returns a recordset with all forced main email addresses for the partners of the given personemail
        recordset
        """
        partner_to_check = self.mapped('partner_id')
        return self.search([('partner_id', 'in', partner_to_check.ids), ('forced_main_address', '=', True)])

    @api.multi
    def compute_state(self):
        """ Will only update the 'state' field of frst.personemail """
        for r in self:

            # Check if 'email' seems valid
            if not r.email or not is_valid_email(r.email):
                if r.state != 'inactive':
                    r.write({'state': 'inactive'})
                continue

            # Check if now() is inside 'gueltig_von' and 'gueltig_bis'
            gueltig_von = fields.datetime.strptime(r.gueltig_von, DEFAULT_SERVER_DATE_FORMAT)
            gueltig_bis = fields.datetime.strptime(r.gueltig_bis, DEFAULT_SERVER_DATE_FORMAT)
            state = 'active' if gueltig_von <= fields.datetime.now() <= gueltig_bis else 'inactive'
            if r.state != state:
                r.write({'state': state})

    # Compute a main_email address and set its field 'main_address' AND update field email of res.partner
    # ATTENTION: 'main_address' will only be set if an email seems valid!
    @api.multi
    def compute_main_address(self):
        """ Will only update the 'main_address' field of frst.personemail """
        start_time = time.time()
        number_of_records = len(self)
        logger.debug("START compute_main_address() for %s records" % number_of_records)

        # Create a new recordset containing all records from self
        # ATTENTION: Maybe the creation of a new recordset is slow and we should only work with ids ?!? To be tested!
        emails = self.env['frst.personemail'] + self
        while len(emails):

            # Find all PersonEmail addresses for this partner
            p_id = emails[0].partner_id.id
            p_emails = emails.search([('partner_id', '=', p_id)], order='last_email_update desc, create_date desc')

            # Find active emails if any
            p_emails_active = p_emails.filtered(lambda m: m.state == 'active')

            # Find forced_main_address active emails if any
            p_emails_active_forced = p_emails_active.filtered(lambda m: m.forced_main_address)
            assert len(p_emails_active_forced) <= 1, "More than one forced main email address for partner %s: %s" \
                                                     "" % (p_id, p_emails_active_forced.ids)

            # Compute the new main email
            if p_emails_active:
                # HINT: p_emails(_active) is already sorted by 'last_email_update desc'
                active_main_email = p_emails_active_forced[0] if p_emails_active_forced else p_emails_active[0]
            else:
                # HINT: In this case p_emails_active is an empty record set
                active_main_email = p_emails_active

            # Update main_email and related res.partner email field
            if active_main_email:

                # Set active_main_email as new main_address if it isn't already the main address
                if not active_main_email.main_address:
                    active_main_email.write({'main_address': True})

                # TODO: THIS IS A FIX FOR FSO MERGE - MAYBE WITH UNKNOWN SIDE EFFECTS ...
                # Check if two or more partner point to the same main email - which is a bug that may be caused by
                # database merges
                wrong_partners = active_main_email.partner_main_email_ids.filtered(
                    lambda p: p.id != active_main_email.partner_id.id
                )
                if wrong_partners:
                    logger.error('More than one Partner for partner_main_email_ids! %s' % wrong_partners.ids)
                    wrong_partners.write({'main_personemail_id': False})
                    logger.info('Recompute main email address for wrong partners with ids: %s' % wrong_partners.ids)
                    wrong_partners.frst_personemail_ids.compute_main_address()

            # Unset 'main_address' for all other email addresses
            p_emails_main = p_emails.filtered(lambda m: m.main_address)
            p_emails_main_deprecated = p_emails_main - active_main_email
            p_emails_main_deprecated.write({'main_address': False})

            # Remove the partner email addresses form the 'emails' recordset and continue the while loop
            records_count_before = len(emails)
            emails = emails - p_emails
            if len(emails) and len(emails) >= records_count_before:
                logger.error("set_main_address() records_before has the same size as records_after!")
                break

        # Finally Log the duration and duration per record
        duration = time.time() - start_time
        duration_per_rec = duration / number_of_records if number_of_records else 0
        logger.debug("END compute_main_address() in %.3f s (%.3f s per record)" % (duration, duration_per_rec))

    # HINT: Make sure the 'main_address' is correct before running compute_partner_email()
    @api.multi
    def compute_partner_email(self):
        start_time = time.time()
        number_of_records = len(self)
        logger.debug("START compute_partner_email() for %s records" % number_of_records)

        emails = self.env['frst.personemail'] + self
        while len(emails):

            # Find main_address
            # HINT: main_address is always an address in state 'active' which means the mail address seems valid!
            p_id = emails[0].partner_id.id
            p_emails = emails.search([('partner_id', '=', p_id)])
            p_active = p_emails.filtered(lambda m: m.state == 'active')
            p_main_address = p_emails.filtered(lambda m: m.main_address)

            if p_main_address:
                assert p_main_address in p_active, "main_address %s not active!" % p_main_address.ids
                # Try a fix if there is more than one main_address
                if len(p_main_address) > 1:
                    p_main_address.compute_main_address()
                    p_main_address = self.search([('partner_id', '=', p_id),
                                                  ('main_address', '=', True)])
                assert len(p_main_address) <= 1, _("Partner with id %s has more than one PartnerEmail main_address!"
                                                   "") % p_id

                # UPDATE
                # ---
                # Update res.partner.'email' from the main_address
                if p_main_address.partner_id.email != p_main_address.email:
                    p_main_address.partner_id.email = p_main_address.email
                # Update res.partner.'main_personemail_id' from the main_address
                if p_main_address.partner_id.main_personemail_id != p_main_address:
                    p_main_address.partner_id.main_personemail_id = p_main_address

            # Clear res.partner.'email' field and 'main_personemail_id' if no active PartnerEmail is left
            else:
                assert not p_active, "Active PersonEmails found but no main_address!"
                # CLEAR
                # ---
                if p_emails[0].partner_id.email:
                    p_emails[0].partner_id.email = False
                if p_emails[0].partner_id.main_personemail_id:
                    p_emails[0].partner_id.main_personemail_id = False

            # Remove the partner email addresses form the 'emails' recordset and continue the while loop
            records_count_before = len(emails)
            emails = emails - p_emails
            if len(emails) and len(emails) >= records_count_before:
                logger.error("compute_partner_email() records_before has the same size as records_after!")
                break

        # Finally Log the duration and duration per record
        duration = time.time() - start_time
        duration_per_rec = duration / number_of_records if number_of_records else 0
        logger.debug("END compute_partner_email() in %.3f s (%.3f s per record)" % (duration, duration_per_rec))

    # ----
    # CRUD
    # ----
    # Helper method for CRUD
    @staticmethod
    def compute_last_email_update_gueltig_bis(values):
        if 'email' in values:
            # Update 'last_email_update'
            if 'last_email_update' not in values:
                values['last_email_update'] = fields.datetime.now()

            # Enable records if email seems valid
            if 'gueltig_bis' not in values:
                email = values.get('email', False)
                if email and is_valid_email(email):
                    values['gueltig_bis'] = '2099-12-31'

        return values

    @api.model
    def create(self, values):

        # Compute 'last_email_update' and 'gueltig_bis' values
        values = self.compute_last_email_update_gueltig_bis(values)

        # Check that no other personemail for this person exists where forced_main_address is set
        if values.get('forced_main_address', None):
            forced = self.get_forced()
            if forced:
                raise ValidationError(_("Another forced main email address (id %s) exists for this partner (id %s)! "
                                        "You must unset the other forced_main_address before setting a new one!"
                                        "" % (forced.ids, values['partner_id'])))

        # Create record in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but the new record exits in the 'res' recordset already
        res = super(FRSTPersonEmail, self).create(values)

        if res:
            # Compute the 'state'
            res.compute_state()

            # Compute the 'main_address'
            # ATTENTION: Run compute_main_address() after compute_state() since it depends on it!
            res.compute_main_address()

            # Compute the field 'email' in res.partner
            # ATTENTION: Run compute_partner_email() after the compute_main_address() since it depends on it!
            res.compute_partner_email()

        return res

    @api.multi
    def write(self, values):

        # Compute 'last_email_update' and 'gueltig_bis' values
        values = self.compute_last_email_update_gueltig_bis(values)

        if values.get('forced_main_address', None):
            forced = self.get_forced()
            if forced:
                raise ValidationError(_("Other forced main email address (id %s) exists already! "
                                        "You must unset other forced_main_address before setting a new one!"
                                        "" % forced.ids))

        # Update (write to) the recordset 'self'
        # ATTENTION: After super 'self' is changed 'res' is only a boolean !
        res = super(FRSTPersonEmail, self).write(values)

        if any(f in values for f in ('email', 'gueltig_von', 'gueltig_bis')):
            # Compute the 'state'
            self.compute_state()

            # Compute the 'main_address'
            # ATTENTION: Run compute_main_address() after compute_state() since it depends on it!
            self.compute_main_address()

            # Update the field 'email' of the res.partner
            # ATTENTION: Run compute_partner_email() after the compute_main_address() since it depends on it!
            self.compute_partner_email()

        return res

    @api.multi
    def unlink(self):

        # Find all partner and partneremails before we delete any of them
        partner = self.mapped('partner_id')

        # HINT: This is a fix for fso_merge to catch if the 'main_personemail_id' was changed by sql and therefore
        #       'main_personemail_id' of the partner points to a a PersonEmail of an other partner!
        partner = partner | self.mapped('partner_main_email_ids')

        partneremails = partner.mapped('frst_personemail_ids')

        # HINT: This is a fix for fso_merge to catch if the 'main_personemail_id' was changed by sql and therefore
        #       'main_personemail_id' of the partner points to a a PersonEmail of an other partner!
        partneremails = partneremails | partner.mapped('main_personemail_id')

        remaining_partneremails = partneremails - self

        partner_with_partneremails_after_unlink = remaining_partneremails.mapped('partner_id')
        partner_without_personmail_after_unlink = partner - partner_with_partneremails_after_unlink

        # ATTENTION: After super 'self' still holds all the records BUT it is marked as deleted! res is just a boolean!
        res = super(FRSTPersonEmail, self).unlink()

        if res:
            # Update remaining PersonEmails
            if remaining_partneremails:
                # Attention: We do not compute the state since the state could not be changed just by removing PEs

                # Compute the main email address 'main_address'
                remaining_partneremails.compute_main_address()

                # Compute the field 'email' in res.partner
                remaining_partneremails.compute_partner_email()

            # Empty field 'email' of res.partner where no PersonEmail is left after the unlink
            if partner_without_personmail_after_unlink:
                partner_without_personmail_after_unlink.write({'email': False})

        return res

    # ---------
    # FSO MERGE
    # ---------
    @api.model
    def _fso_merge_validate(self, rec_to_remove=None, rec_to_keep=None):
        res = super(FRSTPersonEmail, self)._fso_merge_validate(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        logger.info("FSO MERGE FOR PERSONEMAIL: _fso_merge_validate() that the emails are the same!")
        assert rec_to_remove.email.strip().lower() == rec_to_keep.email.strip().lower(), \
                 "E-Mails must match of PersonEmail to keep (%s, %s) and PersonEmail to remove (%s, %s)!" \
                 "" % (rec_to_keep.email, rec_to_keep.id, rec_to_remove.email, rec_to_remove.id)

        return res

    @api.model
    def _fso_merge_empty_write(self, rec_to_keep=None):
        logger.info("FSO MERGE FOR PERSONEMAIL: Write 'email' %s to record-to-keep with id '%s' after merge to update "
                    "main email of the partner!"
                    % (rec_to_keep.email, rec_to_keep.id))
        return rec_to_keep.write({'email': rec_to_keep.email})
