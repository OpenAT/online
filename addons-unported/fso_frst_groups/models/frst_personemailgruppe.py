# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.gruppestate", "frst.checkboxbridgemodel"]

    _group_model_field = 'zgruppedetail_id'
    _target_model_field = 'frst_personemail_id'

    _checkbox_model_field = 'frst_personemail_id.partner_id'
    _checkbox_fields_group_identifier = {
            'newsletter_web': 30104,
        }

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True, ondelete='cascade')
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST PersonEmail",
                                          required=True, ondelete='cascade')

    # Override method from abstract model 'frst.checkboxbridgemodel' to use the 'main_personemail_id' field
    @api.model
    def get_target_model_id_from_checkbox_record(self, checkbox_record=False):
        """ Use the id from the main email address """
        if checkbox_record and checkbox_record.main_personemail_id:
            return checkbox_record.main_personemail_id.id
        else:
            return False