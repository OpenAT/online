# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class MailMassMailingList(models.Model):
    _inherit = "mail.mass_mailing.list"

    zgruppedetail_id = fields.Many2one(string="zGruppeDetail",
                                       comodel_name='frst.zgruppedetail',
                                       domain=['|', ('zgruppe_id.tabellentyp_id', '=', '100110'),
                                                    ('zgruppe_id.sosync_fs_id', '=', '30200'),
                                               ('gui_anzeigen', '=', True)],
                                       help="Create PersonEmailGruppe records and vice versa for mailing list contacts "
                                            "of this mailing list for this zGruppeDetail")

    @api.constrains('zgruppedetail_id')
    def constraint_zgruppedetail_id(self):
        for mlist in self:
            if mlist.zgruppedetail_id:
                assert mlist.list_type == 'email', _("Only lists of type 'email' can have a zGruppeDetail!")

                # Make sure the zGruppeDetail is not changed if list contacts for an other group exists already
                other_group = mlist.contact_ids.filtered(
                    lambda r: r.personemailgruppe_id.zgruppedetail_id != mlist.zgruppedetail_id)
                assert not other_group, _(
                    "List contact(s) %s for different zGruppeDetail exist!") % other_group.ids

                # Make sure a zGruppeDetail is used by exactly one mailing list
                inuse = self.search([('zgruppedetail_id.id', '=', mlist.zgruppedetail_id.id),
                                     ('id', '!=', mlist.id)])
                assert not inuse, _(
                    "This zGruppeDetail is already used by other mailing list(s) %s") % inuse.ids

            else:
                assert not mlist.contact_ids.filtered("personemailgruppe_id"), _(
                    "You can not remove the zGruppeDetail as long as list contacts with PersonEmailGruppe set exist!")
