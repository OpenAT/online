# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTGruppeCheckbox(models.AbstractModel):
    """ Compute zgruppedetail based on checkboxes and vice versa
        USAGE:
            - the group model must inherit from 'frst_gruppestate' abstract class first and then this class
            - the checkbox model must only inherit this class
            - must implement the method gruppecheckbox_config so that it returns the correct config
    """
    _name = "frst.gruppecheckbox"

    @api.model
    def compute_gruppecheckbox_config(self):
        """ Return a dict with class configuration """
        return {}
    # Add a class attribute for the computed config
    gruppecheckbox_config = compute_gruppecheckbox_config()



    @api.multi
    def get_checkbox_model_records(self):
        # TODO
        # Must return a record set
        return

    # TODO: only implement some methods in the checkbox model!
    if True:
        @api.multi
        def set_group(self, group):
            """
            HINT: 'group' is a recordset with one or no record
            HINT: This will only be executed in the checkbox model
            """
            if not self.gruppecheckbox_config:
                return

            for r in self:
                # TODO
                pass

            return True

        @api.multi
        def rem_group(self, group):
            # TODO
            return

        @api.multi
        def checkbox_to_group(self, values):
            values = values or {}
            context = self.env.context or {}

            # Avoid recursive calls
            if 'skipp_checkbox_to_group' in context:
                self.env.context.pop('skipp_checkbox_to_group')
                return
            else:
                self.with_context(skipp_checkbox_to_group=True)

            # Get the gruppecheckbox configuration
            config = self.gruppecheckbox_config
            if not config:
                logger.error('self.gruppecheckbox_config not implemented!')
                return

            # TODO: Only execute if this model is the checkbox model
            #       Maybe this check should be in the crud methods (also) to better understand what is
            #       executed in what model
            # if self.model != config.checkbox_model:
            #     return

            # Only execute if checkbox_fields in values
            checkbox_fields = config['checkbox_fields']
            changed_fields = [f for f in config['checkbox_fields'] if f in values]
            if not changed_fields:
                return

            # Update the groups
            checkbox_model_obj = self.env[config['checkbox_model']]
            for f in changed_fields:
                # HINT: group is a recordset containing a singleton
                group = checkbox_fields[f]
                # Set/Create or Expire/Unsubscribe the group

                checkbox_model_obj.set_group(group) if values[f] else checkbox_model_obj.rem_group(group)

            # Remove recursive run lock in context TODO: check if this makes sense...
            self.env.context.pop('skipp_checkbox_to_group', False)

            return True

    @api.multi
    def group_to_checkbox(self, values):
        values = values or {}
        context = self.env.context or {}

        # TODO
        return

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values, **kwargs):
        values = values or {}
        res = super(FRSTGruppeCheckbox, self).create(values, **kwargs)

        if res:
            # Checkboxes to groups
            # HINT: Will only run in the checkbox model
            res.checkbox_to_group(values)

            # Groups to checkboxes
            # HINT: Will only run in the group model
            res.group_to_checkbox(values)

        return res

    @api.model
    def write(self, values, **kwargs):
        values = values or {}
        res = super(FRSTGruppeCheckbox, self).create(values, **kwargs)

        if res:
            # Checkboxes to groups
            # HINT: Will only run in the checkbox model
            self.checkbox_to_group(values)

            # Groups to checkboxes
            # HINT: Will only run in the group model
            self.group_to_checkbox(values)

        return res

    @api.multi
    def unlink(self):
        # Get related records from checkboxmodel to update after the unlink
        checkbox_model_records = self.get_checkbox_model_records()

        # Unlink the records
        res = super(FRSTGruppeCheckbox, self).unlink()

        if res:
            # Update checkbox fields of checkbox_model_records based on groups after the unlink
            # HINT: Will only run in the group model
            checkbox_model_records.group_to_checkbox()

        return res
