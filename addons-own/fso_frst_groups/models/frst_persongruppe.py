# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.gruppestate", "frst.checkboxbridgemodel", "fso.merge"]

    _group_model_field = 'zgruppedetail_id'
    #_target_model_field = 'partner_id'

    _checkbox_model_field = 'partner_id'
    _checkbox_fields_group_identifier = {
            'donation_deduction_optout_web': 110493,
            'donation_deduction_disabled': 128782,
            'donation_receipt_web': 20168,
            'opt_out': 11102,
        }

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_persongruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                 string="Person",
                                 required=True, ondelete='cascade', index=True)

    @api.model
    def create(self, values):
        res = super(FRSTPersonGruppe, self).create(values)

        # Compute frst blocked
        if res and res.partner_id:
            res.partner_id._set_frst_blocked()

        return res

    @api.multi
    def write(self, values):
        res = super(FRSTPersonGruppe, self).write(values)

        # Compute frst blocked
        if res:
            partner = self.mapped("partner_id")
            partner._set_frst_blocked()

        return res
