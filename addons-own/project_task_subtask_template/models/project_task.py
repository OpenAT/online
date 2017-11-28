# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api
from openerp.exceptions import Warning


class Task(models.Model):
    _inherit = "project.task"

    # Link to subtask templates
    subtask_template_ids = fields.Many2many(string="Checklist Template(s)",
                                            comodel_name='project.task.subtask.template',
                                            relation='rel_subtask_template_task')

    # TODO: Add actions to copy/update the subtasks from the template to the task
    @api.multi
    def import_subtasks(self):
        self.ensure_one()
        task = self
        if not task.subtask_template_ids:
            raise Warning("No Checklist Template(s) selected! Please save the task after you set the template(s)!")

        # Create a new subtask for every template subtask not included in the task already
        # ---
        subtask_obj = self.env['project.task.subtask']

        # List of task subtasks already linked to a template subtask
        task_subtask_template_subtask_ids = [subtask.template_subtask_id.id for subtask in task.subtask_ids
                                             if subtask.template_subtask_id]

        # Cycle through the templates
        for template in task.subtask_template_ids:

            # Cycle through the subtasks of the template
            for template_subtask in template.template_subtask_ids:

                # Create any missing subtask
                if template_subtask.id not in task_subtask_template_subtask_ids:
                    subtask_obj.create({'name': template_subtask.name,
                                        'sequence': template_subtask.sequence,
                                        'extended_description': template_subtask.extended_description,
                                        'task_id': task.id,
                                        'user_id': task.default_user.id,
                                        'template_subtask_id': template_subtask.id,
                                        })
