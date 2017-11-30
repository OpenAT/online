# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.tools import html_escape as escape

class Task(models.Model):
    _inherit = "project.task"

    # Link to subtask templates
    subtask_template_ids = fields.Many2many(string="Checklist Template(s)",
                                            comodel_name='project.task.subtask.template',
                                            relation='rel_subtask_template_task')

    kanban_subtasks_icons = fields.Text(string="Kanban Subtasks", compute='_compute_kanban_subtasks_icons')

    @api.multi
    def _compute_kanban_subtasks_icons(self):
        for record in self:
            result_string1 = ''
            result_string2 = ''
            result_string3 = ''
            for subtask in record.subtask_ids:

                # Shorten Name
                bounding_length = 24
                tmp_list = (subtask.name).split()
                for index in range(len(tmp_list)):
                    if len(tmp_list[index]) > bounding_length:
                        tmp_list[index] = tmp_list[index][:bounding_length] + '...'
                tmp_subtask_name = " ".join(tmp_list)

                if subtask.state == 'todo' and record.env.user == subtask.user_id and record.env.user == subtask.reviewer_id:
                    tmp_string3 = escape(u' {0}'.format(tmp_subtask_name))
                    result_string3 += u'<li><span class="fa fa-edit task-kanban-todo"></span>{}</li>'.format(tmp_string3)

                elif subtask.state == 'todo' and record.env.user == subtask.user_id:
                    tmp_string1 = escape(u'{0} {1}'.format(subtask.reviewer_id.name, tmp_subtask_name))
                    result_string1 += u'<li><span class="fa fa-edit task-kanban-todo"></span> from {}</li>'.format(tmp_string1)

                elif subtask.state == 'todo' and record.env.user == subtask.reviewer_id:
                    tmp_string2 = escape(u'{0} {1}'.format(subtask.user_id.name, tmp_subtask_name))
                    result_string2 += u'<li><span class="fa fa-edit task-kanban-todo"></span> for {}</li>'.format(tmp_string2)

            record.kanban_subtasks_icons = '<ul class="task-kanban-todo">' + result_string1 + result_string3 + result_string2 + '</ul>'

    # Add actions to copy/update the subtasks from the template to the task
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
