# -*- coding: utf-8 -*-
from openerp import models, fields


class FRSTWorkflow(models.Model):
    _inherit = "frst.workflow"

    # Group Settings: frst.zgruppedetail
    # -------------------------------
    approval_workflow_zgruppedetail_ids = fields.One2many(comodel_name='frst.zgruppedetail',
                                                         inverse_name='bestaetigung_workflow',
                                                         string="Group Approval Workflow")
    on_create_workflow_zgruppedetail_ids = fields.One2many(comodel_name='frst.zgruppedetail',
                                                          inverse_name='on_create_workflow',
                                                          string="Group On-Create Workflow")

    # Subscription Settings-Overrides: frst.persongruppe
    # --------------------------------------------------
    approval_workflow_persongruppe_ids = fields.One2many(comodel_name='frst.persongruppe',
                                                         inverse_name='bestaetigung_workflow',
                                                         string="PersonGruppe Approval Workflow")
    on_create_workflow_persongruppe_ids = fields.One2many(comodel_name='frst.persongruppe',
                                                          inverse_name='on_create_workflow',
                                                          string="PersonGruppe On-Create Workflow")

    # Subscription Settings-Overrides: frst.personemailgruppe
    # -------------------------------------------------------
    approval_workflow_personemailgruppe_ids = fields.One2many(comodel_name='frst.personemailgruppe',
                                                              inverse_name='bestaetigung_workflow',
                                                              string="PersonEmailGruppe Approval Workflow")
    on_create_workflow_personemailgruppe_ids = fields.One2many(comodel_name='frst.personemailgruppe',
                                                               inverse_name='on_create_workflow',
                                                               string="PersonEmailGruppe On-Create Workflow")
