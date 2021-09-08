# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
from openerp.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.gruppestate", "frst.checkboxbridgemodel", "fso.merge", "frst.gruppesecurity"]
    _rec_name = 'zgruppedetail_id'
    _description = 'group subscriptions for emails'

    _group_model_field = 'zgruppedetail_id'
    _target_model_field = 'frst_personemail_id'

    _checkbox_model_field = 'frst_personemail_id.partner_id'
    _checkbox_fields_group_identifier = {
            'newsletter_web': 30104,
        }

    # display_name = fields.Char('Subscription Name',
    #                            compute='_compute_display_name',
    #                            search="_search_display_name",
    #                            readonly=True,
    #                            store=False)
    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="Gruppe",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True, ondelete='cascade', index=True)
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST E-Mail",
                                          required=True, ondelete='cascade', index=True)

    partner_frst_blocked = fields.Boolean(string="Partner blocked", readonly=True, index=True)
    partner_frst_blocked_email = fields.Boolean(string="Partner e-mail blocked", readonly=True, index=True)

    # Subscription Group-Settings Overrides
    # -------------------------------------
    # TODO: !!! Constrains for the settings and settings overrides !!!
    bestaetigung_erforderlich = fields.Boolean(string="Approval needed",
                                               default=False,
                                               readonly=True,
                                               help="If this checkbox is set gueltig_von and gueltig_bis will be set "
                                                    "to the past date 09.09.1999 when the group is created to indicate "
                                                    "that an approval is needed before set the group to active.")
    bestaetigung_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn'),
                                                   ('phone_call', "Phone Call"),
                                                   ('workflow', "Fundraising Studio Workflow"),
                                                   ],
                                        readonly=True,
                                        string="Approval Type",
                                        default='doubleoptin')
    bestaetigung_workflow = fields.Many2one(comodel_name="frst.workflow",
                                            inverse_name="approval_workflow_personemailgruppe_ids",
                                            string="Approval Workflow",
                                            readonly=True,
                                            help="Fundraising Studio Approval Workflow")
    on_create_workflow = fields.Many2one(comodel_name="frst.workflow",
                                         inverse_name="on_create_workflow_personemailgruppe_ids",
                                         string="On-Create Workflow",
                                         readonly=True,
                                         help="Fundraising Studio On-Create Workflow")

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

    # @api.multi
    # @api.depends('zgruppedetail_id', 'frst_personemail_id')
    # def _compute_display_name(self):
    #     for r in self:
    #         r.display_name = "%s (FRST-ID: %s) %s" % (
    #             r.zgruppedetail_id.gruppe_lang or r.zgruppedetail_id.gruppe_kurz,
    #             r.zgruppedetail_id.sosync_fs_id if 'sosync_fs_id' in r._fields else '0',
    #             r.frst_personemail_id.email
    #         )
    #
    # def _search_display_name(self, operator, value):
    #     return ['|', '|',
    #               ('zgruppedetail_id.gruppe_lang', operator, value),
    #               ('zgruppedetail_id.sosync_fs_id', operator, value),
    #               ('frst_personemail_id.email', operator, value)
    #             ]
