# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    # Link all PersonEmails
    frst_personemail_ids = fields.One2many(comodel_name="frst.personemail", inverse_name='partner_id',
                                           string="FRST PersonEmail IDS")

    # Link the main PersonEmail
    main_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='partner_main_email_ids',
                                          string="Main Email", readonly=True,
                                          track_visibility='onchange', ondelete='set null')

    # -----------
    # PersonEmail
    # -----------
    @api.multi
    def update_personemail(self):
        """ Creates, activates or deactivates frst.personemail based on field 'email' of the res.partner

        :return: boolean
        """
        for r in self:
            # Reactivate existing PersonEmail
            # Create new PersonEmail
            # Deactivate PersonEmail

            email = r.email.strip().lower() if r.email else ''

            # Email was removed from res.partner -> Only deactivate the current main e-mail address
            # -------------------------------------------------------------------------------------
            # HINT: This was discussed with Martin and Rufus and is considered as the best 'solution' for now
            if not email:
                pe_main_address = r.frst_personemail_ids.filtered(lambda pe: pe.main_address)
                if pe_main_address:
                    yesterday = fields.datetime.now() - timedelta(days=1)
                    pe_main_address.write({'gueltig_bis': yesterday})
                # Continue with next res.partner
                continue

            # Check for existing PersonEmails for the current partner email
            pe_existing = r.frst_personemail_ids.filtered(
                    lambda pe: (pe.email.strip().lower() if pe.email else '' == email)
            )

            # Create a new PersonEmail
            # ------------------------
            if not pe_existing:
                self.env['frst.personemail'].create({'email': r.email, 'partner_id': r.id})

            # Update an existing PersonEmail
            # ------------------------------
            # HINT: This would also 'enable' (status: 'active') the personemail if it is currently 'inactive'
            # ATTENTION: If the email string seems to be invalid the status would still be 'inactive' after this update
            #            This may lead to an empty email field of the res.partner or to an different email if another
            #            'active' PersonEmail exists. Make sure to disallow malformed email strings as early as
            #            possible e.g. in the form validation or at the import!
            elif len(pe_existing) == 1:
                # Only update if there seems to be an email change
                if not r.main_personemail_id or r.main_personemail_id.id != pe_existing.id:
                    pe_existing.write({'last_email_update': fields.datetime.now()})
                else:
                    logger.info("Email %s of res.partner (%s) is already the main_personemail_id." % (email, r.id))

            # More than one PartnerEmail found! Log an Error and continue with next partner
            # -----------------------------------------------------------------------------
            else:
                logger.error("More than one PartnerEmail (IDS %s) found for partner with id %s"
                             "" % (pe_existing.ids, r.id))

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):
        values = values or {}

        res = super(ResPartner, self).create(values)

        # Create a PersonEmail if an email address is set in values
        email = values.get('email', False)
        if res and email:
            res.env['frst.personemail'].create({'email': email, 'partner_id': res.id})

        return res

    @api.multi
    def write(self, values):
        values = values or {}

        # Only update PersonEmail of partners where the email will be changed!
        p_email_changed = False
        if 'email' in values:
            p_email_changed = self.filtered(
                lambda p: p.email.strip().lower() if p.email else '' != values.get('email', '').strip().lower())

        # Write the new email to the partners
        res = super(ResPartner, self).write(values)

        # Create, update or deactivate PersonEmail
        if res and p_email_changed:
            p_email_changed.update_personemail()

        return res
