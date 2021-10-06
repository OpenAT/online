# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.gruppestate", "frst.checkboxbridgemodel", "fso.merge", "frst.gruppesecurity"]

    _rec_name = "subscription_name"

    _group_model_field = 'zgruppedetail_id'
    #_target_model_field = 'partner_id'

    _checkbox_model_field = 'partner_id'
    _checkbox_fields_group_identifier = {
            'donation_deduction_optout_web': 110493,
            'donation_deduction_disabled': 128782,
            'donation_receipt_web': 20168,
            'opt_out': 11102,
        }

    subscription_name = fields.Char('Subscription Name',
                                    compute='_compute_subscription_name',
                                    search="_search_subscription_name",
                                    readonly=True,
                                    store=True)

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_persongruppe_ids',
                                       string="Gruppe",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                 string="Person",
                                 required=True, ondelete='cascade', index=True)

    # partner_frst_blocked = fields.Boolean(related="partner_id.frst_blocked", store=True, readonly=True)
    # partner_frst_blocked_email = fields.Boolean(related="partner_id.frst_blocked_email", store=True, readonly=True)

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

    @api.multi
    @api.depends('zgruppedetail_id', 'partner_id', 'partner_id.name')
    def _compute_subscription_name(self):
        for r in self:
            r.subscription_name = _("%s -> %s") % (
                r.partner_id.name,
                r.zgruppedetail_id.gruppe_lang or r.zgruppedetail_id.gruppe_kurz)

    @api.model
    def compute_all_subscription_name(self):
        logger.info("compute_all_subscription_name for %s" % self._name)
        self.search([])._compute_subscription_name()

    def _search_subscription_name(self, operator, value):
        return ['|', '|',
                  ('zgruppedetail_id.gruppe_lang', operator, value),
                  ('zgruppedetail_id.gruppe_kurz', operator, value),
                  ('partner_id', operator, value)
                ]
