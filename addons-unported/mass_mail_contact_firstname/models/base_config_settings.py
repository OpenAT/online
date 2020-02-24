# -*- coding: utf-8 -*-
# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    mml_contact_names_order = fields.Selection(
        string="mml_contact names order",
        selection="_mml_contact_names_order_selection",
        help="Order to compose mml_contact fullname",
        required=True)
    mml_contact_names_order_changed = fields.Boolean(
        readonly=True, compute="_compute_mml_contact_names_order_changed")

    def _mml_contact_names_order_selection(self):
        return [
            ('last_first', 'Lastname Firstname'),
            ('last_first_comma', 'Lastname, Firstname'),
            ('first_last', 'Firstname Lastname'),
        ]

    def _mml_contact_names_order_default(self):
        return self.env['mail.mass_mailing.contact']._names_order_default()

    @api.multi
    def get_default_mml_contact_names_order(self):
        return {
            'mml_contact_names_order': self.env['ir.config_parameter'].get_param(
                'mml_contact_names_order', self._mml_contact_names_order_default()),
        }

    @api.multi
    @api.depends('mml_contact_names_order')
    def _compute_mml_contact_names_order_changed(self):
        current = self.env['ir.config_parameter'].get_param(
            'mml_contact_names_order', self._mml_contact_names_order_default(),
        )
        for record in self:
            record.mml_contact_names_order_changed = bool(
                record.mml_contact_names_order != current
            )

    @api.onchange('mml_contact_names_order')
    def _onchange_mml_contact_names_order(self):
        self.mml_contact_names_order_changed = self._compute_names_order_changed()

    @api.multi
    def set_mml_contact_names_order(self):
        self.env['ir.config_parameter'].set_param(
            'mml_contact_names_order', self.mml_contact_names_order)

    @api.multi
    def _mml_contacts_for_recalculating(self):
        return self.env['mail.mass_mailing.contact'].search([
            #('is_company', '=', False),
            ('firstname', '!=', False),
            ('lastname', '!=', False),
        ])

    @api.multi
    def action_recalculate_mml_contacts_name(self):
        mml_contacts = self._mml_contacts_for_recalculating()
        _logger.info("Recalculating names for %d mass mail list contacts.", len(mml_contacts))
        mml_contacts._compute_name()
        _logger.info("%d mass mail list contacts updated.", len(mml_contacts))
        return True
