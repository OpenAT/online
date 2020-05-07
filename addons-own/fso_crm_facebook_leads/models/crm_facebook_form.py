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
    personemailgruppe_count = fields.Integer(string="Subscriptions", compute="cmp_personemailgruppe_count")

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

    @api.constrains('zgruppedetail_id', 'frst_zverzeichnis_id', 'force_create_partner', 'state', 'activated')
    def forms_constrains(self):
        for r in self:
            # Make sure force create partner is set!
            if (r.zgruppedetail_id or r.frst_zverzeichnis_id) and not r.force_create_partner:
                raise ValidationError(
                    _("force_create_partner must be checked if a Fundraising Studio Group or the CDS is set!"))
            # Make sure the fields 'zgruppedetail_id' and 'frst_zverzeichnis_id' are set for the state 'active'
            if r.state == 'active' and (not r.zgruppedetail_id or not r.frst_zverzeichnis_id):
                raise ValidationError(
                    _("You must set a Group and a CDS-Record before you can approve/enable the form!"))

    @api.multi
    def cmp_personemailgruppe_count(self):
        for r in self:
            pegs = r.crm_lead_ids.mapped('personemailgruppe_id')
            r.personemailgruppe_count = len(pegs)

    @api.multi
    def button_open_personemailgruppe_graph(self):
        assert self.ensure_one(), "Please select one form only!"

        graph_view_id = self.env.ref('fso_frst_groups.frst_personemailgruppe_graph').id
        tree_view_id = self.env.ref('fso_frst_groups.frst_personemailgruppe_tree').id

        return {
            'domain': [('fb_form_id', '=', self.id), ('crm_lead_ids', 'in', self.crm_lead_ids.ids)],
            'name': 'Subscriptions for Form: "%s"' % self.name,
            'view_type': 'form',
            'view_mode': 'graph,tree',
            'res_model': 'frst.personemailgruppe',
            'view_id': False,
            'views': [(graph_view_id, 'graph'), (tree_view_id, 'tree')],
            'context': "{}",
            'type': 'ir.actions.act_window'
        }

    # Add the frst_zverzeichnis_id to the lead creation values
    @api.multi
    def facebook_data_to_lead_data(self, facebook_lead_data=None):
        res = super(FSOCrmFacebookForm, self).facebook_data_to_lead_data(facebook_lead_data=facebook_lead_data)
        if res and self.frst_zverzeichnis_id:
            logger.info("Adding 'frst_zverzeichnis_id' of the facebook form to the create-lead values!")
            res['frst_zverzeichnis_id'] = self.frst_zverzeichnis_id.id
        return res
