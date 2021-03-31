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

    Usage:
    Add this to group_subscritpion_models like personemailgruppe or persongruppe.
    ATTENTION: It must be ensured that the group field is called 'zgruppedetail_id' or this will fail!
    """
    _name = "frst.gruppesecurity"

    @api.model
    def check_gui_gruppen_bearbeiten_moeglich(self, zgruppedetail, user=None):
        gui_gruppen_bearbeiten_moeglich = zgruppedetail.zgruppe_id.gui_gruppen_bearbeiten_moeglich
        if user is None:
            user = self.env.user
            if user and not gui_gruppen_bearbeiten_moeglich and not user.has_group('base.sosync'):
                raise AccessError(_("You must be in the sosyncer-user-group to create or edit subscriptions "
                                    "for this Fundraising Studio group."))

    @api.model
    def check_nur_eine_gruppe_anmelden(self, zgruppedetail, target_record_id=None):
        subscription_sudo_env = self.sudo()

        nur_eine_gruppe_anmelden = zgruppedetail.zgruppe_id.nur_eine_gruppe_anmelden
        if not nur_eine_gruppe_anmelden:
            return

        other_groups_in_folder = zgruppedetail.zgruppe_id.zgruppedetail_ids - zgruppedetail
        if not other_groups_in_folder:
            return

        if self._name == 'frst.persongruppe':
            target_record_field = 'partner_id'
        elif self._name == 'frst.personemailgruppe':
            target_record_field = 'frst_personemail_id'
        else:
            raise ValueError("Unknown model:  %s!" % self._name)
        if target_record_id is None:
            self.ensure_one()
            target_record_id = self[target_record_field].id
        other_subscritpions = subscription_sudo_env.search([
                (target_record_field, '=', target_record_id),
                ('zgruppedetail_id.id', 'in', other_groups_in_folder.ids)
            ],
            limit=1)

        if other_subscritpions:
            raise ValidationError("Only one subscription is allowed for groups in the group folder %s! Existing"
                                  "subscription: %s" % (zgruppedetail.zgruppe_id, other_subscritpions.ids))

    @api.model
    def create(self, vals):
        zgruppedetail_id = vals.get('zgruppedetail_id', None)
        if zgruppedetail_id:
            zgruppedetail = self.env['frst.zgruppedetail'].browse(zgruppedetail_id)

            # check_gui_gruppen_bearbeiten_moeglich
            self.check_gui_gruppen_bearbeiten_moeglich(zgruppedetail)

            # check_nur_eine_gruppe_anmelden
            if self._name == 'frst.persongruppe':
                target_record_field = 'partner_id'
            elif self._name == 'frst.personemailgruppe':
                target_record_field = 'frst_personemail_id'
            else:
                raise ValueError("Unknown model:  %s!" % self._name)
            if vals.get(target_record_field):
                self.check_nur_eine_gruppe_anmelden(zgruppedetail, vals[target_record_field])

        return super(FRSTGruppeSecurity, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(FRSTGruppeSecurity, self).write(vals)
        if res:
            protected = self.filtered(lambda r: not r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
            for r in protected:
                r.check_gui_gruppen_bearbeiten_moeglich(r.zgruppedetail_id)
                r.check_nur_eine_gruppe_anmelden(r.zgruppedetail_id)
        return res

    @api.multi
    def unlink(self):
        protected = self.filtered(lambda r: not r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
        for r in protected:
            r.check_gui_gruppen_bearbeiten_moeglich(r.zgruppedetail_id)
            r.check_nur_eine_gruppe_anmelden(r.zgruppedetail_id)
        return super(FRSTGruppeSecurity, self).unlink()
