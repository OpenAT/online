# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api


class ProjectTaskSubtaskTemplate(models.Model):
    _name = 'project.task.subtask.template'
    _inherit = ['ir.needaction_mixin']

    _order = 'sequence'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence")

    # Template description
    description = fields.Text(string="Description")

    # Link to subtasks used (created) in this template
    template_subtask_ids = fields.One2many(string="Items", delete='',
                                           comodel_name="project.task.subtask", inverse_name='subtask_template_id')

    # Tasks that use this template
    template_task_ids = fields.Many2many(string="Used by Tasks",
                                         comodel_name="project.task",
                                         relation="rel_subtask_template_task")

    @api.multi
    def unlink(self):

        # Unlink related subtasks
        for template in self:
            template.template_subtask_ids.unlink()

        # Unlink the template(s)
        return super(ProjectTaskSubtaskTemplate, self).unlink()
