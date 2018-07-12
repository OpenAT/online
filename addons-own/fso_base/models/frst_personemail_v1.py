# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import time

from openerp.addons.fso_base.tools.validate import is_valid_email

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
    and shoul not be used anymore. They may even get deleted in the near future.

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

    It is still do be discussed whether or not a user can completely delete/deactivate a PersonEmail if this
    e-mail is re-imported into Fundraising Studio from external sources. If so the 'active' field would be an obvious
    choice.

    user account login and e-mail addresses
    ---------------------------------------
    In most cases the e-mail address of a person will be used for the login field of the related res.user.
    If a person (res.partner) creates an account (res.user) automatically by a click on a token link or manually by
    registration on the website we would suggest or even force the login to be the email address of the field email in
    res.partner.

    Therefore this should be the same as the current PersonEmail marked as main_email at the time of account creation.

    If the main PersonEmail changes after the account creation we will NOT change the login! How to change an existing
    login is something that must still be discussed by the dev team.
    """
    _name = "frst.personemail"
    _rec_name = "email"

    email = fields.Char(string="E-Mail", required=True,
                        help="This field should normally NEVER change after record creation. The only exception"
                             "to this rule would be a quick typo fix after manual creation in FRST GUI.")
    last_email_update = fields.Datetime(string="Last Email Update", readonly=True,
                                        help="Holds the last datetime the email field changed either by the"
                                             "GUI a website form or an import from an external data source",
                                        index=True)

    # Partner related to this e-mail address
    person_id = fields.Many2one(string="Person", required=True,
                                comodel_name="res.partner", inverse_name='frst_personemail_ids',
                                help="This field should normally NEVER change after record creation. The only exception"
                                     "to this rule would be a quick typo fix after manual creation in FRST GUI.",
                                index=True)

    # DISABLED: because not available in Fundraising Studio
    # active = fields.Char(string="Active",
    #                      default=True,
    #                      help="This field is NOT available in Fundraising Studio!"
    #                           "PersonEmail will no longer be available if not active!")

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
                             compute="compute_state", store=True,
                             help="A PersonEmail has a state of active if the e-mail format seems valid and now is "
                                  "inside gueltig_von and gueltig_bis")

    # Main email address indicator
    main_address = fields.Boolean(string="Main Address", readonly=True,
                                  # compute="compute_main_address", store=True,
                                  help="This indicates if the record is the primary active e-mail address. "
                                       "It will be used in webforms or exports where only one e-mail is allowed."
                                       "It should match with the email field in res.partner!")

    # DISABLED: After a talk to Harry he suggested to not use forced_main_address!
    # forced_main_address = fields.Boolean("Force as Main Address")
    # last_forced_main_address_set = fields.Datetime(string="Last Forced Main Address Set",
    #                                                compute="_compute_last_forced_main_address_set", store=True,
    #                                                help="Only set if last_forced_main_address is enabled!",
    #                                                readonly=True)

    # DISABLED: Active months of current year
    # ATTENTION: After a talk to devs and rufus we decided to not use the month grid for PersonEmail!
    # january = fields.Boolean(string="January", default=True)
    # february = fields.Boolean(string="February", default=True)
    # march = fields.Boolean(string="March", default=True)
    # april = fields.Boolean(string="April", default=True)
    # may = fields.Boolean(string="May", default=True)
    # june = fields.Boolean(string="June", default=True)
    # july = fields.Boolean(string="July", default=True)
    # august = fields.Boolean(string="August", default=True)
    # september = fields.Boolean(string="September", default=True)
    # october = fields.Boolean(string="October", default=True)
    # november = fields.Boolean(string="November", default=True)
    # december = fields.Boolean(string="December", default=True)

    # -------
    # METHODS
    # -------
    @api.multi
    def compute_state(self):
        for r in self:

            # Check if email address seems valid (if not set to inactive)
            if not r.email or not is_valid_email(r.email):
                if r.state != 'inactive':
                    r.state = 'inactive'
                continue

            # Check if now is inside gueltig_von and gueltig_bis
            gueltig_von = fields.datetime.strptime(r.gueltig_von, DEFAULT_SERVER_DATE_FORMAT)
            gueltig_bis = fields.datetime.strptime(r.gueltig_bis, DEFAULT_SERVER_DATE_FORMAT)
            state = 'active' if gueltig_von <= fields.datetime.now() <= gueltig_bis else 'inactive'
            if r.state != state:
                r.state = state

    # The main email address must be an active email address
    # It is either the last email address where 'email' was changed OR the one where forced_main_address was last set
    # @api.depends('state', 'last_email_update')

    # HINT: The main_address must be recomputed if the 'state' or the 'last_email_update' field changes
    @api.multi
    def compute_main_address(self):
        start_time = time.time()
        number_of_records = len(self)
        logger.info("START set_main_email_address() for %s records" % number_of_records)

        emails = self.env['frst.personemail'] + self
        # emails = self
        logger.info("emails is self: %s" % bool(emails is self))
        while emails:

            # Find all PersonEmail addresses for this partner
            p_id = emails[0].person_id.id
            p_emails = emails.search([('person_id', '=', p_id)], order='last_email_update desc, create_date desc')

            # Find active_main_email if any
            p_emails_active = p_emails.filtered(lambda m: m.state == 'active')
            if p_emails_active:
                # HINT: p_emails(_active) is already sorted by 'last_email_update desc'
                active_main_email = p_emails_active[0]
            else:
                # HINT: In this case p_emails_active is an empty record set
                active_main_email = p_emails_active

            # Update main_email and related res.partner email field
            if active_main_email:
                # Set active_main_email as new main_address
                if not active_main_email.main_address:
                    active_main_email.write({'main_address': True})

            # Unset 'main_address' for all other email addresses
            p_emails_main = p_emails.filtered(lambda m: bool(m.main_address))
            p_emails_main_deprecated = p_emails_main - active_main_email
            p_emails_main_deprecated.write({'main_address': False})

            # Remove the partner email addresses form the 'emails' recordset and continue the while loop
            records_before = len(emails)
            emails = emails - p_emails
            records_after = len(emails)
            if records_before and records_before >= records_after:
                logger.error("set_main_address() records_before has the same size as records_after!")
                break

        # Finally Log the duration and duration per record
        duration = time.time() - start_time
        duration_per_rec = duration / number_of_records if number_of_records else 0
        logger.info("END set_main_email_address() in %.3f ms (%.3f ms per record)" % (duration, duration_per_rec))

        return True

    @api.multi
    def compute_partner_email(self):
        # Todo
        # Set email field of res.partner
        # if active_main_email.person_id.email != active_main_email.email:
        #     active_main_email.person_id.write({'email': active_main_email.email})
        pass

    # ------------
    # CRUD NEW TRY
    # ------------
    @api.model
    def compute_values(self, values):
        if 'email' in values:
            # Update 'last_email_update'
            if 'last_email_update' not in values:
                values['last_email_update'] = fields.datetime.now()

            # Enable records if email seems valid
            if 'gueltig_bis' not in values:
                email = values.get('email', False)
                if email and is_valid_email(email):
                    values['gueltig_bis'] = '2099-12-31'


    @api.model
    def create(self, values):

        # Check if 'last_email_update' and 'gueltig_bis' should be added to the values
        values = self.compute_values(values)

        # Create the email address in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but the new record exits in the 'res' recordset already
        res = super(FRSTPersonEmail, self).create(values)
        logger.info("create() before len(res) %s " % len(res))

        if res:
            # Compute the main email address
            res.set_main_address()
        logger.info("create() after len(res) %s " % len(res))

        return res

    @api.multi
    def write(self, values):

        if 'email' in values:
            # Update 'last_email_update'
            if 'last_email_update' not in values:
                values['last_email_update'] = fields.datetime.now()

            # Enable records if email seems valid
            if 'gueltig_bis' not in values:
                email = values.get('email', False)
                if email and is_valid_email(email):
                    values['gueltig_bis'] = '2099-12-31'

        # Update (write to) the recordset 'self'
        # ATTENTION: After super 'self' is changed 'res' is only a boolean !
        res = super(FRSTPersonEmail, self).write(values)

        # Compute the 'state' if any field that may alter it is in values
        if res:
            if any(f in values for f in ('email', 'gueltig_von', 'gueltig_bis')):
                self.compute_state()

        # Compute the 'main_address' if any field that may alter it is in values
        if res:
            if any(f in values for f in ('email', 'last_email_update', 'gueltig_von', 'gueltig_bis')):
                self.compute_main_address()

        return res

    # # ----
    # # CRUD
    # # ----
    # @api.model
    # def create(self, values):
    #
    #     # Create the email address in the current environment (memory only right now i guess)
    #     # ATTENTION: self is still empty but the BPK exits in the 'res' recordset already
    #     res = super(FRSTPersonEmail, self).create(values)
    #     logger.info("before len(self) %s " % len(self))
    #
    #     if res:
    #         # Compute the main email address
    #         res.set_main_email_address()
    #     logger.info("after len(self) %s " % len(self))
    #
    #     return res
    #
    # @api.multi
    # def write(self, values):
    #
    #     # ATTENTION: !!! After this 'self' is changed (in memory i guess)
    #     #                'res' is only a boolean !!!
    #     res = super(FRSTPersonEmail, self).write(values)
    #     logger.info("before len(self) %s " % len(self))
    #
    #     # Compute the main email address
    #     if res:
    #         self.set_main_email_address()
    #
    #     logger.info("after len(self) %s " % len(self))
    #
    #     return res


# Inverse for PersonEmail
class ResPartner(models.Model):
    _inherit = 'res.partner'

    frst_personemail_ids = fields.One2many(comodel_name="frst.personemail", inverse_name='person_id',
                                           string="FRST PersonEmail IDS")

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):

        # Create the email address in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but the new record exits in the 'res' recordset already
        res = super(ResPartner, self).create(values)

        email = values.get('email', False)
        if email:
            # Create a new PersonEmail
            res.env['frst.personemail'].write({'email': email, 'person_id': res.id})

        return res

