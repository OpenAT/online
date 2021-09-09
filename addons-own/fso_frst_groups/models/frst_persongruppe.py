# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.gruppestate", "frst.checkboxbridgemodel", "fso.merge", "frst.gruppesecurity"]

    _rec_name = "zgruppedetail_id"

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
                                       string="Gruppe",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                 string="Person",
                                 required=True, ondelete='cascade', index=True)

    # partner_frst_blocked = fields.Boolean(related="partner_id.frst_blocked", store=True, readonly=True)
    # partner_frst_blocked_email = fields.Boolean(related="partner_id.frst_blocked_email", store=True, readonly=True)

    # Subscription Group-Settings Overrides
    # -------------------------------------
    # TODO: !!! Constrains for the settings and settings overrides !!!
    # TODO: !!! bestaetigung_erforderlich must be a selection field to explicitly show the override !!!
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
                                        string="Approval Type",
                                        readonly=True,
                                        default='doubleoptin')
    bestaetigung_workflow = fields.Many2one(comodel_name="frst.workflow",
                                            inverse_name="approval_workflow_persongruppe_ids",
                                            string="Approval Workflow",
                                            readonly=True,
                                            help="Fundraising Studio Approval Workflow")
    on_create_workflow = fields.Many2one(comodel_name="frst.workflow",
                                         inverse_name="on_create_workflow_persongruppe_ids",
                                         string="On-Create Workflow",
                                         readonly=True,
                                         help="Fundraising Studio On-Create Workflow")

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
