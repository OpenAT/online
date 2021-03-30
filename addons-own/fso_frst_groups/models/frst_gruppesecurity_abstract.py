# -*- coding: utf-8 -*-
from copy import deepcopy
from openerp import models, fields, api
from openerp.exceptions import AccessError
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
    def check_gui_gruppen_bearbeiten_moeglich(self, gui_gruppen_bearbeiten_moeglich, user=None):
        if user is None:
            user = self.env.user
            if user and not gui_gruppen_bearbeiten_moeglich and not user.has_group('base.sosync'):
                raise AccessError(_("You must be in the sosyncer-user-group to create or edit subscriptions "
                                    "for this Fundraising Studio group."))

    @api.model
    def create(self, vals):
        zgruppedetail_id = vals.get('zgruppedetail_id', None)
        if zgruppedetail_id:
            zgruppedetail = self.env['frst.zgruppedetail'].browse(zgruppedetail_id)
            self.check_gui_gruppen_bearbeiten_moeglich(zgruppedetail.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
        return super(FRSTGruppeSecurity, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(FRSTGruppeSecurity, self).write(vals)
        if res:
            protected = self.filtered(lambda r: not r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
            for r in protected:
                r.check_gui_gruppen_bearbeiten_moeglich(r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
        return res

    @api.multi
    def unlink(self):
        protected = self.filtered(lambda r: not r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
        for r in protected:
            r.check_gui_gruppen_bearbeiten_moeglich(r.zgruppedetail_id.zgruppe_id.gui_gruppen_bearbeiten_moeglich)
        return super(FRSTGruppeSecurity, self).unlink()
