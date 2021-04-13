# -*- coding: utf-8 -*-
from copy import deepcopy
from openerp import models, fields, api
from openerp.exceptions import AccessError, ValidationError
from openerp.tools.translate import _
import time
import logging
logger = logging.getLogger(__name__)


class FRSTGruppeSecurity(models.AbstractModel):
    """ Check if the modification of group subscriptions is allowed based on the zGruppe field
    'gui_gruppen_bearbeiten_moeglich'.

    The naming is missleading! Should be named frst_subscription_security_abstract!

    Usage:
    Add this to group_subscription_models like personemailgruppe or persongruppe.
    ATTENTION: It must be ensured that the group field is called 'zgruppedetail_id' or this will fail!
    """
    _name = "frst.gruppesecurity"

    @api.model
    def check_gui_gruppen_bearbeiten_moeglich(self):
        protected = self.filtered(lambda r: not r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)

        if protected and self.env.user and not self.env.user.has_group('base.sosync'):
            raise AccessError(_("You must be in the sosyncer-user-group to create, edit or delete the subscription(s):"
                                " %s") % protected)

    @api.model
    def check_nur_eine_gruppe_anmelden(self):
        # Determine group subscription target record field
        if self._name == 'frst.persongruppe':
            group_target_field = 'partner_id'
        elif self._name == 'frst.personemailgruppe':
            group_target_field = 'frst_personemail_id'
        else:
            raise ValueError("Unknown model:  %s!" % self._name)

        # Filter out the subscriptions to check
        subscriptions_to_check = self.filtered(lambda r: r.zgruppedetail_id.zgruppe_id.nur_eine_gruppe_anmelden)
        if not subscriptions_to_check:
            return

        # Search for other active subscriptions for the group subscription target record (e.g. a res.partner)
        for r in subscriptions_to_check:
            group_target_id = r[group_target_field].id
            groups_in_folder = r.zgruppedetail_id.zgruppe_id.zgruppedetail_ids
            active = self.sudo().search([
                (group_target_field, '=', group_target_id),
                ('zgruppedetail_id.id', 'in', groups_in_folder.ids),
                ('state', 'not in', ['unsubscribed', 'expired'])
                ],
                limit=2)
            if len(active) >= 2:
                raise ValidationError("Only one group can have an active subscription for groups in the group folder %s"
                                      " ! Active subscriptions: %s" % (r.zgruppedetail_id.zgruppe_id,
                                                                       active))
            # TODO: Performance optimization: We may remove all other subscriptions for this subscription target
            #                                 in subscriptions_to_check if they are for groups_in_folder

    @api.model
    def create(self, vals):
        record = super(FRSTGruppeSecurity, self).create(vals)
        if record:
            record.check_gui_gruppen_bearbeiten_moeglich()
            record.check_nur_eine_gruppe_anmelden()

        return record

    @api.multi
    def write(self, vals):
        res = super(FRSTGruppeSecurity, self).write(vals)
        if res:
            self.check_gui_gruppen_bearbeiten_moeglich()
            self.check_nur_eine_gruppe_anmelden()

        return res

    @api.multi
    def unlink(self):
        for r in self:
            r.check_gui_gruppen_bearbeiten_moeglich()

        return super(FRSTGruppeSecurity, self).unlink()
