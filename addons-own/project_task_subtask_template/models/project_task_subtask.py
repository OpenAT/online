# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
import logging
logger = logging.getLogger(__name__)

class ProjectTaskSubtask(models.Model):
    _inherit = 'project.task.subtask'

    sequence = fields.Integer(string="Sequence", index=1)

    # Add a long description field
    extended_description = fields.Text(string="Extended Description", translate=True)

    # For subtasks used in subtask templates
    # Link to templates
    subtask_template_id = fields.Many2one(string="Template",
                                          comodel_name='project.task.subtask.template')

    # For subtasks used in tasks
    # HINT: Keep a reference to the original subtask from a template
    template_subtask_id = fields.Many2one(string='Origin', comodel_name='project.task.subtask')

    task_template_subtask_ids = fields.One2many(string='Used by Task Subtasks',
                                                comodel_name='project.task.subtask', inverse_name='template_subtask_id')

    template_subtask_id_template_id = fields.Many2one(string="Origin Template",
                                                      comodel_name='project.task.subtask.template',
                                                      related='template_subtask_id.subtask_template_id', store=True)

    # Remove required for some fields
    user_id = fields.Many2one(required=False)
    task_id = fields.Many2one(required=False)

    # Order Subtasks by sequence field
    _order = 'sequence'

    # Overwrite default methods to make the subtasks for templates work
    @api.model
    def create(self, vals):

        # Just create the subtask if it is for a template without the extra functions of project_task_subtask
        # HINT: https://rhettinger.wordpress.com/2011/05/26/super-considered-super/
        #       logger.info(ProjectTaskSubtask.__mro__)
        if 'subtask_template_id' in vals:
            # Create the subtask without any additional code
            logger.info("Template Subtask will be created!")

            # Add the correct sequence number
            # TODO: make a small function out of it to not duplicate the code
            hseq = self.search([], limit=1, order='sequence DESC')
            if hseq:
                logger.info("Subtask highest sequence found: %s!" % hseq.sequence)
                logger.info("Sequence in vals: %s!" % vals.get('sequence'))
                if vals.get('sequence') <= hseq.sequence:
                    vals['sequence'] = hseq.sequence + 1
                    logger.info("Sequence computed: %s!" % vals.get('sequence'))
            else:
                vals['sequence'] = 1

            # Call create method of models.Model
            logger.info("Final Sequence for subtask: %s!" % vals.get('sequence'))
            res = super(models.Model, self).create(vals)
        else:
            # Create the subtask with any code from the addon project_task_subtask
            logger.info("Regular Subtask will be created!")

            # Since we removed 'required' from some fields we need to check them here
            if not all((vals.get('user_id'), vals.get('task_id'))):
                raise Warning("Fields 'user_id' and 'task_id' are required!")

            # Add the correct sequence number
            # TODO: make a small function out of it to not duplicate the code
            hseq = self.search([], limit=1, order='sequence DESC')
            if hseq:
                logger.info("Subtask highest sequence found: %s!" % hseq.sequence)
                logger.info("Sequence in vals: %s!" % vals.get('sequence'))
                if vals.get('sequence') <= hseq.sequence:
                    vals['sequence'] = hseq.sequence + 1
                    logger.info("Sequence computed: %s!" % vals.get('sequence'))
            else:
                vals['sequence'] = 1

            # Call create method of addon project_task_subtask
            res = super(ProjectTaskSubtask, self).create(vals)

        return res

    @api.multi
    def write(self, vals):
        # If subtask_template_id will be set or is already set
        if vals.get('subtask_template_id') or (self.subtask_template_id and 'subtask_template_id' not in vals):
            logger.info("Template Subtask will be updated!")
            res = super(models.Model, self).write(vals)
        else:
            logger.info("Regular Subtask will be updated!")

            # Update records in current environment (memory only)
            res = super(ProjectTaskSubtask, self).write(vals)

            # Since we removed 'required' from some fields we need to check them here
            for r in self:
                if not all((r.user_id, r.task_id)):
                    raise Warning("Fields 'user_id' and 'task_id' are required!")

        # Return res so that the changes can be written to the database
        return res
