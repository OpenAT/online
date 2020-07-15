# -*- coding: utf-8 -*-
from openerp import models, fields, api


class FRSTPersonEmail(models.Model):
    _inherit = "frst.personemail"

    personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='frst_personemail_id',
                                            string="FRST PersonEmailGruppe IDS")

    # @api.model
    # def create(self, vals):
    #     context = self.env.context or {}
    #
    #     res = super(FRSTPersonEmail, self).with_context(
    #         skipp_update_main_personemail_id_and_checkboxes=True).create(vals)
    #
    #     if res and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners = res.mapped('partner_id')
    #         partners.update_main_personemail_id_and_checkboxes()
    #     return res
    #
    # @api.multi
    # def write(self, vals):
    #     context = self.env.context or {}
    #
    #     res = super(FRSTPersonEmail, self).with_context(
    #         skipp_update_main_personemail_id_and_checkboxes=True).write(vals)
    #
    #     if self and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners = self.mapped('partner_id')
    #         partners.update_main_personemail_id_and_checkboxes()
    #     return res
    #
    # @api.multi
    # def unlink(self):
    #     context = self.env.context or {}
    #     partners = False
    #     if self and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners = self.mapped('partner_id')
    #
    #     res = super(FRSTPersonEmail, self).with_context(
    #         skipp_update_main_personemail_id_and_checkboxes=True).unlink()
    #
    #     if partners and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners.update_main_personemail_id_and_checkboxes()
    #     return res

    # Inactivate all PersonEmailGruppe if the PersonEmail gets inactivated
    @api.multi
    def write(self, vals):
        res = super(FRSTPersonEmail, self).write(vals)

        # Check on any change of gueltig_von or gueltig_bis for any non inactivated PersonEmailGruppe
        if res and 'gueltig_von' in vals or 'gueltig_bis' in vals:
            # Get all inactive emails in self
            inactive_emails = self.filtered(lambda m: m.state == 'inactive')
            inactive_emails_group_assignments = inactive_emails.mapped('personemailgruppe_ids')
            active_group_assignments = inactive_emails_group_assignments.filtered(
                lambda peg: peg.state in ['subscribed', 'approved'])
            # Transfer the gueltig_von and gueltig_bis in the vals for the personemail to the active personemailgruppe
            if active_group_assignments:
                peg_vals = {}
                if 'gueltig_von' in vals:
                    peg_vals['gueltig_von'] = vals['gueltig_von']
                if 'gueltig_bis' in vals:
                    peg_vals['gueltig_bis'] = vals['gueltig_bis']
                active_group_assignments.write(peg_vals)

        return res
