# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.gruppestate"]

    FRST_GRUPPE_TO_CHECKBOX = {
        110493: 'donation_deduction_optout_web',
        128782: 'donation_deduction_disabled',
        20168: 'donation_receipt_web',  # DEPRECATED!
        # TODO: Email Sperrgruppe (11102)
    }

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_persongruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True, ondelete='cascade')
    partner_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                 string="Person",
                                 required=True, ondelete='cascade')

    @api.model
    def gruppecheckbox_config(self):
        bridge_model = 'frst.persongruppe'
        bridge_model_group_field = 'zgruppedetail_id'
        bridge_model_group_model = 'frst.zgruppedetail'

        checkbox_model = 'res.partner'
        checkbox_model_bridge_model_field = 'persongruppe_ids'

        checkbox_fields = {
            'donation_deduction_optout_web': 110493,
            'donation_deduction_disabled': 128782,
            'donation_receipt_web': 20168,
            # TODO: Email Sperrgruppe (11102)
        }
        for f, sosync_fs_id in checkbox_fields.iteritems():
            group_model = self.env[bridge_model_group_model].sudo()
            group = group_model.search([('sosync_fs_id', '=', sosync_fs_id)], limit=1)
            checkbox_fields[f] = group

        return {'bridge_model': bridge_model,
                'bridge_model_group_field': bridge_model_group_field,
                'bridge_model_group_model': bridge_model_group_model,
                'checkbox_model': checkbox_model,
                'checkbox_model_bridge_model_field': checkbox_model_bridge_model_field,
                'checkbox_fields': checkbox_fields,
                }

    @api.model
    def create(self, values, **kwargs):
        res = super(FRSTPersonGruppe, self).create(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            partner = res.mapped('partner_id')
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_persongruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def write(self, values, **kwargs):
        res = super(FRSTPersonGruppe, self).write(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            partner = self.mapped('partner_id')
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_persongruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def unlink(self):
        partner = self.mapped('partner_id')

        res = super(FRSTPersonGruppe, self).unlink()

        # Update res.partner checkboxes
        if res and partner:
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_persongruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res


