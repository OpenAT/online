# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTGruppeState(models.AbstractModel):
    """ Compute the state based on 'gueltig_von' and 'gueltig_bis' Fields

    HINT: Simply overwrite the methods if you need a more complex computation of the state
    """
    _name = "frst.gruppestate"

    state = fields.Selection(selection=[('subscribed', 'Subscribed'),
                                        ('unsubscribed', 'Unsubscribed'),
                                        ('expired', 'Expired')],
                             string="State", readonly=True)

    steuerung_bit = fields.Boolean(string="Steuerung Bit", default=True,
                                   help="If not set: Person is explicitly excluded/unsubscribed from group!")
    gueltig_von = fields.Date("GueltigVon", required=True, default=lambda s: fields.datetime.now())
    gueltig_bis = fields.Date("GueltigBis", required=True, default=lambda s: fields.date(2099, 12, 31))

    @api.multi
    def compute_state(self):
        # ATTENTION: Make sure only the field state is written in this method and no other field! (see CRUD)
        mandatory_fields = ('gueltig_von', 'gueltig_bis')
        assert all(hasattr(self, f) for f in mandatory_fields), "Fields 'gueltig_von' and 'gueltig_bis' must exist!"

        for r in self:
            now = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Compute 'steuerung_bit'
            steuerung_bit = True
            if hasattr(r, 'steuerung_bit'):
                steuerung_bit = r.steuerung_bit

            # Compute state
            if r.gueltig_von <= now <= r.gueltig_bis:
                state = 'subscribed' if steuerung_bit else 'unsubscribed'
            else:
                state = 'expired'

            # Write state
            if r.state != state:
                r.write({'state': state})
        return True

    @api.multi
    def compute_all_states(self):
        # ATTENTION: Make sure only the field state is written in this method and no other field! (see CRUD)
        now = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

        # Search for subscribed groups
        subscribed_domain = [
            ('gueltig_von', '<=', now),
            ('gueltig_bis', '>=', now),
            ('state', 'not in', ('subscribed',))
        ]
        if hasattr(self, 'steuerung_bit'):
            subscribed_domain.append(('steuerung_bit', '=', True))
        subscribed = self.sudo().search(subscribed_domain)
        subscribed.write({'state': 'subscribed'})

        # Search for unsubscribed groups
        unsubscribed_domain = [
            ('gueltig_von', '<=', now),
            ('gueltig_bis', '>=', now),
            ('state', 'not in', ('unsubscribed',))
        ]
        if hasattr(self, 'steuerung_bit'):
            unsubscribed_domain.append(('steuerung_bit', '=', False))
        unsubscribed = self.sudo().search(unsubscribed_domain)
        unsubscribed.write({'state': 'unsubscribed'})

        # Search for expired groups
        expired = self.sudo().search([
            ('state', 'not in', ('expired',)),
            '|',
              ('gueltig_von', '>', now),
              ('gueltig_bis', '<', now),
        ])
        expired.write({'state': 'expired'})
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
        res = super(FRSTGruppeState, self).create(values, **kwargs)
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
