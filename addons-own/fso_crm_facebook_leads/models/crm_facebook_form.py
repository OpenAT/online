# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class FSOCrmFacebookForm(models.Model):
    _inherit = 'crm.facebook.form'

    force_create_partner = fields.Boolean(string="Force Create Partner",
                                          default=True,
                                          help="If enabled leads will be created in state 'opportunity' and therefore "
                                               "create a partner and link to the lead! This is useful for "
                                               "Fundraising Studio where a partner is needed to create the lead as an"
                                               "'Aktion'")

    # HINT: "tabellentyp_id = 100110" means e-mail which in fact stands for PersonEmailGruppe stuff
    zgruppedetail_id = fields.Many2one(string="Fundraising Studio Group",
                                       comodel_name="frst.zgruppedetail", inverse_name='crm_fb_form_ids',
                                       ondelete="set null", index=True,
                                       domain=[('zgruppe_id', '!=', False),
                                               ('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       help="Fundraising Studio E-Mail Group")

    # HINT: "verzeichnistyp_id = False" means the CDS record is not a folder but a file
    frst_zverzeichnis_id = fields.Many2one(string="Fundraising Studio CDS",
                                           comodel_name="frst.zverzeichnis", inverse_name='crm_fb_form_ids',
                                           ondelete="set null", index=True,
                                           readonly=False,
                                           domain=[('verzeichnistyp_id', '=', False)],
                                           help="Fundraising Studio CDS List/File. Right now this must match the "
                                                "Fundraising Studio Group CDS setting but this may change in the "
                                                "future")

    @api.onchange('zgruppedetail_id', 'frst_zverzeichnis_id', 'frst_zverzeichnis_id')
    def forms_onchange(self):
        for r in self:
            # Make sure a new partner will be created on lead creation if a group or cds is set
            if r.zgruppedetail_id or r.frst_zverzeichnis_id:
                r.force_create_partner = True
            # Sync the FRST cds setting from the group if not set already
            if not r.frst_zverzeichnis_id and r.zgruppedetail_id and r.zgruppedetail_id.frst_zverzeichnis_id:
                r.frst_zverzeichnis_id = r.zgruppedetail_id.frst_zverzeichnis_id

    @api.constrains('zgruppedetail_id', 'frst_zverzeichnis_id', 'frst_zverzeichnis_id')
    def forms_constrains(self):
        for r in self:
            # Make sure force create partner is set!
            if (r.zgruppedetail_id or r.frst_zverzeichnis_id) and not r.force_create_partner:
                raise ValidationError(
                    _("force_create_partner must be checked if a Fundraising Studio Group or the CDS is set!"))

    # Add the frst_zverzeichnis_id to the lead creation values
    @api.multi
    def facebook_data_to_lead_data(self, facebook_lead_data=None):
        res = super(FSOCrmFacebookForm, self).facebook_data_to_lead_data(facebook_lead_data=facebook_lead_data)
        if res and self.frst_zverzeichnis_id:
            res['frst_zverzeichnis_id'] = self.frst_zverzeichnis_id.id
        return res
