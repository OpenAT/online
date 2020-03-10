# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.tools.translate import _

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
                                       domain=[('zgruppe_id', '!=', False),
                                               ('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       help="Fundraising Studio E-Mail Group")

    # HINT: "verzeichnistyp_id = False" means the CDS record is not a folder but a file
    frst_zverzeichnis_id = fields.Many2one(string="Fundraising Studio CDS",
                                           comodel_name="frst.zverzeichnis", inverse_name='crm_fb_form_ids',
                                           domain=[('verzeichnistyp_id', '=', False)],
                                           readonly=True,
                                           help="Fundraising Studio CDS List/File. Right now this must match the "
                                                "Fundraising Studio Group CDS setting but this may change in the "
                                                "future")

    @api.onchange('zgruppedetail_id', 'frst_zverzeichnis_id', 'frst_zverzeichnis_id')
    def forms_onchange(self):
        for r in self:
            if r.zgruppedetail_id or r.frst_zverzeichnis_id:
                r.force_create_partner = True
            # Sync the cds leave setting from the group if set
            # ATTENTION: This link may be removed at any time to allow setting a different cds leave for the leads than
            #            the group or set the cds leave without any group set!
            r.frst_zverzeichnis_id = r.zgruppedetail_id.frst_zverzeichnis_id if r.zgruppedetail_id else False

    @api.constrains('zgruppedetail_id', 'frst_zverzeichnis_id', 'frst_zverzeichnis_id')
    def forms_constrains(self):
        for r in self:
            # ATTENTION: This link may be removed at any time to allow setting a different cds leave for the leads than
            #            the group or set the cds leave without any group set! (Is set in onchange also)
            if r.frst_zverzeichnis_id:
                assert r.frst_zverzeichnis_id == r.zgruppedetail_id.frst_zverzeichnis_id, _(
                    "The CDS setting in the Fundraising Studio Group must match the CDS setting of this form!")
            else:
                assert not r.frst_zverzeichnis_id, _(
                    "CDS must be unset if no Fundraising Studio Group is set!")

            # Make sure force create partner is set!
            if r.zgruppedetail_id or r.frst_zverzeichnis_id:
                assert r.force_create_partner, _("force_create_partner must be checked if a Fundraising Studio Group "
                                                 "or the CDS is set!")
