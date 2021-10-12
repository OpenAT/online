# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _
import openerp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
from openerp.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.gruppestate", "frst.checkboxbridgemodel", "fso.merge", "frst.gruppesecurity"]
    _rec_name = 'subscription_name'
    _description = 'group subscriptions for emails'

    _group_model_field = 'zgruppedetail_id'
    _target_model_field = 'frst_personemail_id'

    _checkbox_model_field = 'frst_personemail_id.partner_id'
    _checkbox_fields_group_identifier = {
            'newsletter_web': 30104,
        }

    subscription_name = fields.Char('Subscription Name', readonly=True)
    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="Gruppe",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True, ondelete='cascade', index=True)
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST E-Mail",
                                          required=True, ondelete='cascade', index=True)

    partner_frst_blocked = fields.Boolean(string="Partner blocked", readonly=True, index=True)
    partner_frst_blocked_email = fields.Boolean(string="Partner e-mail blocked", readonly=True, index=True)

    @api.multi
    def _compute_state(self):
        self.ensure_one()
        r = self

        super(FRSTPersonEmailGruppe, self)._compute_state()

        partner_frst_blocked = r.frst_personemail_id.partner_id.frst_blocked
        if r.partner_frst_blocked != partner_frst_blocked:
            r.partner_frst_blocked = partner_frst_blocked

        partner_frst_blocked_email = r.frst_personemail_id.partner_id.frst_blocked_email
        if r.partner_frst_blocked_email != partner_frst_blocked_email:
            r.partner_frst_blocked_email = partner_frst_blocked_email

    @api.model
    def scheduled_compute_state(self):
        super(FRSTPersonEmailGruppe, self).scheduled_compute_state()

        # partner_frst_blocked TRUE
        logger.info("Fix partner_frst_blocked=True")
        pegs_block_to_set = self.search([
            ('partner_frst_blocked', '=', False),
            ('frst_personemail_id.partner_id.frst_blocked', '!=', False)
        ])
        logger.info("Found %s personemailgruppe to SET partner_frst_blocked!" % len(pegs_block_to_set))
        pegs_block_to_set.write({'partner_frst_blocked': True})

        # partner_frst_blocked FALSE
        logger.info("Fix partner_frst_blocked=False")
        pegs_block_to_unset = self.search([
            ('partner_frst_blocked', '!=', False),
            ('frst_personemail_id.partner_id.frst_blocked', '=', False)
        ])
        logger.info("Found %s personemailgruppe to UNSET partner_frst_blocked!" % len(pegs_block_to_unset))
        pegs_block_to_unset.write({'partner_frst_blocked': False})

        # partner_frst_blocked_email FALSE
        logger.info("Fix partner_frst_blocked_email=False")
        pegs_block_email_to_unset = self.search([
            ('partner_frst_blocked_email', '!=', False),
            ('frst_personemail_id.partner_id.frst_blocked_email', '=', False)
        ])
        logger.info("Found %s personemailgruppe to UNSET partner_frst_blocked_email!" % len(pegs_block_email_to_unset))
        pegs_block_email_to_unset.write({'partner_frst_blocked_email': False})

        # partner_frst_blocked_email TRUE
        logger.info("Fix partner_frst_blocked_email=True")
        pegs_block_email_to_set = self.search([
            ('partner_frst_blocked_email', '=', False),
            ('frst_personemail_id.partner_id.frst_blocked_email', '!=', False)
        ])
        logger.info("Found %s personemailgruppe to SET partner_frst_blocked_email!" % len(pegs_block_email_to_set))
        pegs_block_email_to_set.write({'partner_frst_blocked_email': True})

    @api.constrains('gueltig_von', 'gueltig_bis', 'steuerung_bit')
    def constraint_inactive_personemail(self):
        for r in self:
            if r.frst_personemail_id.state != 'active' and r.state in ['subscribed', 'approved']:
                raise ValidationError(_("Only inactive groups (personemailgruppe %s) are allowed for an inactive "
                                        "e-mail (personemail %s)!") % (r.id, r.frst_personemail_id.id))

    # Override method from abstract model 'frst.checkboxbridgemodel' to use the 'main_personemail_id' field
    @api.model
    def get_target_model_id_from_checkbox_record(self, checkbox_record=False):
        """ Use the id from the main email address """
        if checkbox_record and checkbox_record.main_personemail_id:
            return checkbox_record.main_personemail_id.id
        else:
            return False

    @api.multi
    @api.depends('zgruppedetail_id', 'frst_personemail_id')
    def _compute_subscription_name(self):
        for r in self:
            subscription_name = _("%s -> %s") % (
                r.frst_personemail_id.email,
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
        res = super(FRSTPersonEmailGruppe, self).create(vals)

        if res and 'subscription_name' not in vals:
            if 'zgruppedetail_id' in vals or 'frst_personemail_id' in vals:
                res._compute_subscription_name()

        return res

    @api.multi
    def write(self, vals):
        res = super(FRSTPersonEmailGruppe, self).write(vals)

        if res and 'subscription_name' not in vals:
            if 'zgruppedetail_id' in vals or 'frst_personemail_id' in vals:
                res._compute_subscription_name()

        return res
