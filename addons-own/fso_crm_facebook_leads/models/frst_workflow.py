# -*- coding: utf-8 -*-
from openerp import models, fields


class FRSTWorkflow(models.Model):
    _inherit = "frst.workflow"

    approval_workflow_fb_field_ids = fields.One2many(comodel_name='crm.facebook.form.field',
                                                     inverse_name='bestaetigung_workflow',
                                                     string="Facebook Lead Fields Approval Workflow")
    on_create_workflow_fb_field_ids = fields.One2many(comodel_name='crm.facebook.form.field',
                                                      inverse_name='on_create_workflow',
                                                      string="Facebook Lead Fields On-Create Workflow")
