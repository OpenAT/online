# -*- coding: utf-8 -*-
from openerp import models, fields, api


class FRSTPersonEmail(models.Model):
    _inherit = "frst.personemail"

    personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='frst_personemail_id',
                                            string="FRST PersonEmailGruppe IDS")

    # Inactivate all PersonEmailGruppe if the PersonEmail gets inactivated
    @api.multi
    def write(self, vals):
        res = super(FRSTPersonEmail, self).write(vals)

        # Check on any change of gueltig_von or gueltig_bis for any non inactivated PersonEmailGruppe
        if res and 'gueltig_von' in vals or 'gueltig_bis' in vals:

            # Get all inactive personemails in self
            inactive_emails = self.filtered(lambda m: m.state == 'inactive')
            inactive_emails_group_assignments = inactive_emails.mapped('personemailgruppe_ids')
            active_group_assignments = inactive_emails_group_assignments.filtered(
                lambda peg: peg.state in ['subscribed', 'approved'])

            # Transfer the gueltig_von and gueltig_bis in the vals for the personemail to the active personemailgruppe
            # to inactivate the related personemailgruppe also
            if active_group_assignments:
                peg_vals = {}
                if 'gueltig_von' in vals:
                    peg_vals['gueltig_von'] = vals['gueltig_von']
                if 'gueltig_bis' in vals:
                    peg_vals['gueltig_bis'] = vals['gueltig_bis']
                active_group_assignments.write(peg_vals)

        return res
