# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "frst.checkboxmodel"]

    _bridge_model_fields = ('persongruppe_ids', 'main_email_personemailgruppe_ids')

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       track_visibility='onchange',
                                       string="FRST PersonGruppe IDS")

    # Main e-mail groups (related field)
    main_email_personemailgruppe_ids = fields.One2many(related='main_personemail_id.personemailgruppe_ids',
                                                       track_visibility='onchange',
                                                       string="Main Email Groups", readonly=True)

    frst_blocked = fields.Boolean("FRST: Partner Blocked", readonly=True,
                                  help="Is in one or more active 'Fundraising Studio Personensperrgruppen'")
    frst_blocked_email = fields.Boolean("FRST: E-Mail Channel Blocked", readonly=True,
                                        help="Is in one or more active 'Fundraising Studio Personensperrgruppen' "
                                             "for the channel e-mail")

    # Count person groups
    partner_persongruppe_count = fields.Integer(string="Personengruppenanzahl",
                                                compute="_compute_frst_persongruppe_count")

    # Count all e-mail groups
    partner_personemailgruppe_count = fields.Integer(string="E-Mail-Gruppen Anzahl",
                                                     compute="_compute_frst_personemailgruppe_count")

    @api.multi
    @api.depends('persongruppe_ids')
    def _compute_frst_persongruppe_count(self):
        for r in self:
            r.partner_persongruppe_count = len(r.persongruppe_ids) or 0

    @api.multi
    @api.depends('frst_personemail_ids')
    def _compute_frst_personemailgruppe_count(self):
        for r in self:
            pegs = r.mapped("frst_personemail_ids.personemailgruppe_ids")
            r.partner_personemailgruppe_count = len(pegs) if pegs else 0

    @api.multi
    def button_open_personemailgruppe(self):
        assert self.ensure_one(), "Please select one partner only!"
        action = self.env['ir.actions.act_window'].for_xml_id('fso_frst_groups', 'frst_personemailgruppe_action')
        action['domain'] = [('frst_personemail_id.partner_id', '=', self.id)]
        action['context'] = {'default_frst_personemail_id': self.main_personemail_id.id,
                             'default_gueltig_von': fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
                             'default_gueltig_bis': fields.date(2099, 12, 31).strftime(DEFAULT_SERVER_DATE_FORMAT),
                             }
        return action

    # HINT: Changes to 'frst.persongruppe' will trigger the computation also!
    @api.multi
    def _set_frst_blocked(self):
        for r in self:
            blocked = False
            email_blocked = False
            # Only compute this if the syncer addon is already installed
            if 'sosync_fs_id' in self.env['frst.zgruppe']._fields:
                for pg in r.persongruppe_ids:
                    # Only check active subscriptions for active (=enabled in this frst instance) groups
                    if pg.state in ['subscribed', 'approved'] and pg.zgruppedetail_id.gui_anzeigen:
                        # All groups in the "Personensperren" group folder
                        if not blocked:
                            if pg.zgruppedetail_id.zgruppe_id.sosync_fs_id == 11000:
                                blocked = True
                        # The group "E-Mail Kanalsperre"
                        if not email_blocked:
                            if pg.zgruppedetail_id.sosync_fs_id == 11102:
                                email_blocked = True
            r.frst_blocked = blocked
            r.frst_blocked_email = email_blocked

    def scheduled_set_frst_blocked(self):
        if 'sosync_fs_id' not in self.env['frst.zgruppe']._fields:
            logger.error("fso_sosync seems not to be installed! Skipping scheduled_set_frst_blocked()")
            return

        # VERSION 2
        pg_obj = self.env['frst.persongruppe']

        # FRST_BLOCKED
        # ------------
        logger.info("Searching for partner that are blocked in Fundraising Studio (Personensperre)")
        pg_blocked = pg_obj.search([
            ('state', 'in', ['subscribed', 'approved']),
            ('zgruppedetail_id.gui_anzeigen', '=', True),
            ('zgruppedetail_id.zgruppe_id.sosync_fs_id', '=', 11000),
        ])
        logger.info("Found %s frst.persongruppe" % len(pg_blocked))
        # HINT: Only one of the records in persongruppe_ids must meet the domain condition(s) to return the partner
        partner_blocked = self.search([('persongruppe_ids', 'in', pg_blocked.ids)])
        partner_blocked_ids = partner_blocked.ids
        logger.info("Found %s partner that are blocked (in a Personensperrgruppe)" % len(partner_blocked_ids))

        # Set frst_blocked
        to_block = self.search([('id', 'in', partner_blocked_ids), ('frst_blocked', '=', False)])
        logger.info("Found %s partner to block" % len(to_block))
        to_block.write({'frst_blocked': True})
        logger.info("Fixed %s partner with frst_blocked: True" % len(to_block))

        # Unset frst_blocked
        # Attention: 'not in' is very slow on postgres with large lists - therefore i work around this...
        # to_release = self.search([('id', 'not in', partner_blocked_ids), ('frst_blocked', '=', True)])
        all_blocked = self.search([('frst_blocked', '=', True)])
        to_release_ids = set(all_blocked.ids) - set(partner_blocked_ids)
        logger.info("Found %s partner to release" % len(to_release_ids))
        self.browse(list(to_release_ids)).write({'frst_blocked': False})
        logger.info("Fixed %s partner with frst_blocked: False" % len(to_release_ids))

        # FRST_BLOCKED_EMAIL
        # ------------------
        logger.info("Searching for partner with 'Kanalsperre E-Mail'")
        pg_blocked_email = pg_obj.search([
            ('state', 'in', ['subscribed', 'approved']),
            ('zgruppedetail_id.gui_anzeigen', '=', True),
            ('zgruppedetail_id.sosync_fs_id', '=', 11102),
        ])
        # partner_blocked_email = pg_blocked_email.mapped('partner_id')
        partner_blocked_email = self.search([('persongruppe_ids', 'in', pg_blocked_email.ids)])
        logger.info("Found %s partner with 'Kanalsperre E-Mail'" % len(partner_blocked_email))

        # Set frst_blocked_email
        to_block_email = self.search([('id', 'in', partner_blocked_email.ids), ('frst_blocked_email', '=', False)])
        to_block_email.write({'frst_blocked_email': True})
        logger.info("Fixed %s partner with frst_blocked_email: True" % len(to_block_email))

        # Unset frst_blocked
        # Attention: 'not in' is very slow on postgres with large lists - therefore i work around this...
        # to_release_email = self.search([('id', 'not in', partner_blocked_email.ids),
        #                                 ('frst_blocked_email', '=', True)])
        all_blocked_email = self.search([('frst_blocked_email', '=', True)])
        to_release_email_ids = set(all_blocked_email.ids) - set(partner_blocked_email.ids)
        self.browse(list(to_release_email_ids)).write({'frst_blocked_email': False})
        logger.info("Fixed %s partner with frst_blocked_email: False" % len(to_release_email_ids))

    @api.model
    def create(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(ResPartner, self).create(values)

        # Checkboxes to groups for all bridge models
        if 'skipp_checkbox_to_group' not in context:
            res.checkbox_to_group(values)

        # Compute frst blocked
        if 'persongruppe_ids' in values and res:
            res._set_frst_blocked()

        return res

    @api.multi
    def write(self, values):
        values = values or {}
        context = self.env.context or {}

        # if 'email' in values:
        #     email_only = {'email': values.pop('email')}
        #     res = super(ResPartner, self).write(email_only)

        res = super(ResPartner, self).write(values)

        # Checkboxes to groups
        if 'skipp_checkbox_to_group' not in context:
            self.checkbox_to_group(values)

        # Update checkboxes by groups if main email changes for frst.personemail bridge model
        if 'main_personemail_id' in values:
            self.group_to_checkbox()

        # Compute frst blocked
        if 'persongruppe_ids' in values and res:
            self._set_frst_blocked()

        return res
