# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
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
                             string="State", readonly=True)

    steuerung_bit = fields.Boolean(string="Steuerung Bit", default=True,
                                   help="If not set: Person is explicitly excluded/unsubscribed from this group!")
    gueltig_von = fields.Date("GueltigVon", required=True, default=lambda s: fields.datetime.now())
    gueltig_bis = fields.Date("GueltigBis", required=True, default=lambda s: fields.date(2099, 12, 31))

    # Group approval information
    bestaetigt_am_um = fields.Datetime("Bestaetigt", readonly=True)
    bestaetigt_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn'),
                                                 ('phone_call', "Phone Call"),
                                                 ],
                                        string="Bestaetigungs Typ", readonly=True)
    bestaetigt_herkunft = fields.Char("Bestaetigungsherkunft", readonly=True,
                                      help="E.g.: The link or the workflow process")

    @api.multi
    def compute_state(self):
        # ATTENTION: Make sure only the field state is written in this method and no other field!
        #            Check the recursion query in in the CRUD methods for infos why!
        mandatory_fields = ('gueltig_von', 'gueltig_bis')
        assert all(f in self._fields for f in mandatory_fields), "Fields 'gueltig_von' and 'gueltig_bis' must exist!"

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
                r.write({'state': state})
        return True

    @api.multi
    def compute_all_states(self, optimized=True):
        # ATTENTION: Make sure only the field state is written in this method and no other field! (see CRUD)
        start = time.time()

        # This is the 'safe' but slow non-optimized version
        # =================================================
        if not optimized:
            all_groups = self.sudo().search([])
            logger.info("Compute group state for %s records for model %s" % (len(all_groups), self.__class__.__name__))
            all_groups.compute_state()
            logger.info("Compute group state for %s records for model %s done in %.6f seconds"
                        "" % (len(all_groups), self.__class__.__name__, time.time()-start))
            return True

        # Optimized version (way faster!)
        # ===============================
        logger.info("Compute group state with optimized routine for model %s" %  self.__class__.__name__)

        # Get current datetime
        now = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

        # Check approval_pending
        # ----------------------
        approval_pending_domain = [
            ('gueltig_von', '=', self._approval_pending_date),
            ('gueltig_bis', '=', self._approval_pending_date),
            ('state', 'not in', ('approval_pending',))
        ]
        if 'steuerung_bit' in self._fields:
            approval_pending_domain.append(('steuerung_bit', '=', True))
        approval_pending = self.sudo().search(approval_pending_domain)
        approval_pending.write({'state': 'approval_pending'})

        # Check subscribed
        # ----------------
        subscribed_domain = [
            ('gueltig_von', '<=', now),
            ('gueltig_bis', '>=', now),
            ('bestaetigt_am_um', '=', False),
            ('state', 'not in', ('subscribed',))
        ]
        if 'steuerung_bit' in self._fields:
            subscribed_domain.append(('steuerung_bit', '=', True))
        subscribed = self.sudo().search(subscribed_domain)
        subscribed.write({'state': 'subscribed'})

        # Check approved
        # --------------
        approved_domain = [
            ('gueltig_von', '<=', now),
            ('gueltig_bis', '>=', now),
            ('bestaetigt_am_um', '!=', False),
            ('state', 'not in', ('approved',))
        ]
        if 'steuerung_bit' in self._fields:
            approved_domain.append(('steuerung_bit', '=', True))
        approved = self.sudo().search(approved_domain)
        approved.write({'state': 'approved'})

        # Check unsubscribed
        # ------------------
        if 'steuerung_bit' in self._fields:
            unsubscribed_domain = [
                ('gueltig_von', '<=', now),
                ('gueltig_bis', '>=', now),
                ('steuerung_bit', '=', False),
                ('state', 'not in', ('unsubscribed',))
            ]
            unsubscribed = self.sudo().search(unsubscribed_domain)
            unsubscribed.write({'state': 'unsubscribed'})

        # Check expired
        # -------------
        expired = self.sudo().search([
            '&',
            '&',
            ('state', 'not in', ('expired',)),
            '|',
                ('gueltig_von', '!=', self._approval_pending_date),
                ('gueltig_bis', '!=', self._approval_pending_date),
            '|',
                ('gueltig_von', '>', now),
                ('gueltig_bis', '<', now),
        ])
        expired.write({'state': 'expired'})

        logger.info("Compute group state with optimized routine for model %s done in %.6f seconds"
                    "" % (self.__class__.__name__, time.time()-start))

        return True

    @api.model
    def scheduled_compute_all_states(self):
        self.compute_all_states()
        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values, **kwargs):
        values = values or dict()

        # Check 'approval_needed' field of the group (frst.zgruppedetail)
        if 'gueltig_von' not in values and 'gueltig_bis' not in values:

            # Get Grpup
            group = False
            if hasattr(self, '_group_model_field') and self._group_model_field:
                group_model_field_name = self._group_model_field
                group_id = values.get(group_model_field_name, False)
                if group_id and hasattr(self, '_fields'):
                    group_model_field = self._fields.get(group_model_field_name, False)
                    if hasattr(group_model_field, 'comodel_name') and group_model_field.comodel_name:
                        group = self.env[group_model_field.comodel_name].search([('id', '=', group_id)])

            # Check bestaetigung_erforderlich setting of group
            if hasattr(group, 'bestaetigung_erforderlich'):
                if group.bestaetigung_erforderlich:
                    values['gueltig_von'] = self._approval_pending_date
                    values['gueltig_bis'] = self._approval_pending_date
            else:
                logger.error("Could not check 'bestaetigung_erforderlich' at creation of bm_group with vals %s"
                             "" % str(values))

        # Create the record
        res = super(FRSTGruppeState, self).create(values, **kwargs)

        # Update the state
        if res and not values.keys() == ['state']:
            res.compute_state()

        return res

    @api.multi
    def write(self, values, **kwargs):
        values = values or dict()
        res = super(FRSTGruppeState, self).write(values, **kwargs)
        if res and not values.keys() == ['state']:
            self.compute_state()
        return res
