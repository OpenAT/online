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
    main_personemail_id = fields.Many2one(comodel_name="frst.personemail", string="Main Email", readonly=True)

    # -----------
    # PersonEmail
    # -----------
    @api.multi
    def update_personemail(self):
        """ Creates, activates or deactivates frst.personemail based on field 'email' of the res.partner

        :return: boolean
        """
        for r in self:
            if r.email:
                partnermail_exits = r.frst_personemail_ids.filtered(lambda m: m.email == r.email)

                # Activate PartnerEmail
                if partnermail_exits:
                    # Do nothing if more than one email was found which is considered as an error
                    # HINT: This should be fixed automatically by Fundraising Studio in a night run
                    #       (FRST merges same mail addresses per partner)
                    if len(partnermail_exits) > 1:
                        logger.error("More than one PartnerEmail %s found for partner with id %s"
                                     "" % (r.id, partnermail_exits[0].email))
                        continue

                    # Make sure this PartnerMail is the main_address by changing the write_date
                    if not partnermail_exits.main_address:
                        partnermail_exits.write({'email': r.email})

                # Create PartnerEmail
                else:
                    self.env['frst.personemail'].create({'email': r.email, 'partner_id': r.id})

            # Deactivate PartnerEmail
            else:
                # Deactivate only the main_address for this partner
                # HINT: This was discussed with Martin and Rufus and is considered as the best 'solution' for now
                main_address = r.frst_personemail_ids.filtered(lambda m: m.main_address)
                if main_address:
                    yesterday = fields.datetime.now() - timedelta(days=1)
                    main_address.write({'gueltig_bis': yesterday})

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

        res = super(ResPartner, self).write(values)

        # Update or create a PersonEmail
        if res and 'email' in values:
            self.update_personemail()

        return res
