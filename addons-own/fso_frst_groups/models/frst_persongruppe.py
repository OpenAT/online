# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _
import openerp

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

    subscription_name = fields.Char('Subscription Name', readonly=True)

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
            subscription_name = _("%s -> %s") % (
                r.partner_id.name,
                r.zgruppedetail_id.gruppe_lang or r.zgruppedetail_id.gruppe_kurz)
            r.write({'subscription_name': subscription_name})

    @api.model
    def compute_all_subscription_name(self, batch=1000):
        logger.info("compute_all_subscription_name for %s" % self._name)

        missing = True
        max_runs = 1000
        while missing and max_runs:
            max_runs = max_runs - 1
            with openerp.api.Environment.manage():
                with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    missing = self.with_env(new_env).search([('subscription_name', '=', False)], limit=batch)
                    logger.info("Compute subscription_name for %s records. (runs left %s)" % (len(missing), max_runs))
                    missing._compute_subscription_name()
                    new_env.cr.commit()

    @api.model
    def create(self, vals):
        res = super(FRSTPersonGruppe, self).create(vals)
        if res and 'subscription_name' not in vals:
            if 'zgruppedetail_id' in vals or 'partner_id' in vals:
                res._compute_subscription_name()

    @api.multi
    def write(self, vals):
        res = super(FRSTPersonGruppe, self).write(vals)
        if res and 'subscription_name' not in vals:
            if 'zgruppedetail_id' in vals or 'partner_id' in vals:
                for r in self:
                    r._compute_subscription_name()
