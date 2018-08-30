# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.gruppestate"]

    FRST_GRUPPE_TO_CHECKBOX = {
        30104: 'newsletter_web',
    }

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True, ondelete='cascade')
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST PersonEmail",
                                          required=True, ondelete='cascade')

    @api.model
    def compute_gruppecheckbox_config(self):
        bridge_model = 'frst.personemailgruppe'
        bridge_model_group_field = 'zgruppedetail_id'
        bridge_model_group_model = 'frst.zgruppedetail'

        checkbox_model = 'res.partner'
        checkbox_model_bridge_model_field = 'main_personemail_id.personemailgruppe_ids'

        checkbox_fields = {
            'newsletter_web': 30104,
        }
        for f, sosync_fs_id in checkbox_fields.iteritems():
            group_model = self.env[bridge_model_group_model].sudo()
            group = group_model.search([('sosync_fs_id', '=', sosync_fs_id)], limit=1)
            checkbox_fields[f] = group

        return {'bridge_model': bridge_model,
                'bridge_model_group_field': bridge_model_group_field,
                'bridge_model_group_model': bridge_model_group_model,
                'checkbox_model': checkbox_model,
                'checkbox_model_bridge_model_field': checkbox_model_bridge_model_field,
                'checkbox_fields': checkbox_fields,
                }

    @api.model
    def create(self, values, **kwargs):
        res = super(FRSTPersonEmailGruppe, self).create(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            email = res.mapped('frst_personemail_id')

            if email.main_address:
                partner = email.mapped('partner_id')
                for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                    partner.update_checkbox_by_personemailgruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def write(self, values, **kwargs):
        res = super(FRSTPersonEmailGruppe, self).write(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            email = self.mapped('frst_personemail_id')

            if email.main_address:
                partner = email.mapped('partner_id')
                for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                    partner.update_checkbox_by_personemailgruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def unlink(self):
        email = self.mapped('frst_personemail_id')

        if email:
            partner = email.mapped('partner_id')

        res = super(FRSTPersonEmailGruppe, self).unlink()

        # Update res.partner checkboxes
        if email and res and partner:
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_personemailgruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res
