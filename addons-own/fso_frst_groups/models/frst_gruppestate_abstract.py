# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import time
import logging
logger = logging.getLogger(__name__)


class FRSTGruppeState(models.AbstractModel):
    """
    This model is added to the groupbridgemodels e.g.: frst.personemailgruppe and extends them with a state
    and various other fields

    State Descriptions
    ------------------
    approval_pending:   The Group is assigned but waiting for approval
                        CONDITION: gueltig_von and gueltig_bis is set to past-date '09.09.1999' and steuerung_bit
                        FRST ACTIVE: False
                        FSON CHECKBOX: True !!!

    subscribed:         The group is active
                        CONDITION: gueltig_von <= now <= gueltig_bis and not bestaetigt_am_um and steuerung_bit
                        FRST ACTIVE: True
                        FSON CHECKBOX: True

    approved:           The group is subscribed and approved
                        CONDITION: (gueltig_von <= now <= gueltig_bis) and bestaetigt_am_um and steuerung_bit
                        FRST ACTIVE: True
                        FSON CHECKBOX: True

    unsubscribed:       Explicitly (on purpose) unsubscribed/excluded from this group
                        CONDITION: (gueltig_von <= now <= gueltig_bis) and not steuerung_bit
                        FRST ACTIVE: False
                        FSON CHECKBOX: False

    expired:            The group is expired (now outside of gueltig_von and gueltig_bis)
                        CONDITION: not (gueltig_von <= now <= gueltig_bis)
                        FRST ACTIVE: False
                        FSON CHECKBOX: False

    TODO: Discuss if 'expired' or 'unsubscribed' is more important? Right now expired beats unsubscribed which seems ok?
    TODO: Discuss what is expected if steuerung_bit is False set but group is expired with approval_pending_date?!?

    HINT: Simply overwrite the methods if you need a more complex computation of the state
    """
    _name = "frst.gruppestate"

    _approval_pending_date = fields.date(1999, 9, 9).strftime(DEFAULT_SERVER_DATE_FORMAT)

    state = fields.Selection(selection=[('approval_pending', 'Waiting for Approval'),
                                        ('subscribed', 'Subscribed'),
                                        ('approved', 'Approved'),
                                        ('unsubscribed', 'Unsubscribed'),
                                        ('expired', 'Expired')],
                             string="State", readonly=True, compute="compute_state", store=True)

    steuerung_bit = fields.Boolean(string="Steuerung Bit", default=True,
                                   help="If not set: Person is explicitly excluded/unsubscribed from this group!")

    # ATTENTION: The default is now computed below in the create() method!
    gueltig_von = fields.Date("GueltigVon", required=True)
    gueltig_bis = fields.Date("GueltigBis", required=True)

    # Group approval information
    bestaetigt_am_um = fields.Datetime("Bestaetigt", readonly=True)
    bestaetigt_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn'),
                                                 ('phone_call', 'Phone Call'),
                                                 ('workflow', 'Fundraising Studio Workflow'),
                                                 ],
                                      string="Bestaetigungs Typ", readonly=True)
    bestaetigt_herkunft = fields.Char("Bestaetigungsherkunft", readonly=True,
                                      help="E.g.: The link or the workflow process")

    @api.depends('gueltig_von', 'gueltig_bis', 'steuerung_bit')
    def compute_state(self):
        for r in self:
            now = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Compute 'steuerung_bit'
            steuerung_bit = True
            if hasattr(r, 'steuerung_bit'):
                steuerung_bit = r.steuerung_bit

            # Compute state
            if r.gueltig_von <= now <= r.gueltig_bis:
                if not steuerung_bit:
                    state = 'unsubscribed'
                else:
                    state = 'approved' if r.bestaetigt_am_um else 'subscribed'
            else:
                if steuerung_bit and r.gueltig_von == r.gueltig_bis == self._approval_pending_date:
                    state = 'approval_pending'
                else:
                    state = 'expired'

            # Write state
            if r.state != state:
                r.state = state

        return True

    @api.model
    def create(self, vals):

        # Compute the default values for 'gueltig_von' and 'gueltig_bis' if none where provided!
        if 'gueltig_von' not in vals and 'gueltig_bis' not in vals:
            # Default values for gueltig_von and gueltig_bis
            gueltig_von = fields.datetime.now()
            gueltig_bis = fields.date(2099, 12, 31)

            # Set to 'approval needed magic date' if bestaetigung_erforderlich is set in the group
            group_model_field_name = self._group_model_field
            vals_group_id = vals.get(group_model_field_name, False)
            if vals_group_id:
                group_model_name = self._fields.get(group_model_field_name).comodel_name
                group = self.env[group_model_name].browse([vals_group_id])
                if group.bestaetigung_erforderlich:
                    gueltig_von = self._approval_pending_date
                    gueltig_bis = self._approval_pending_date

            # Add to vals
            vals['gueltig_von'] = gueltig_von
            vals['gueltig_bis'] = gueltig_bis

        # Create the record
        return super(FRSTGruppeState, self).create(vals)
