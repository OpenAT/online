# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTCheckboxBridgeModel(models.AbstractModel):
    _name = "frst.checkboxbridgemodel"

    # Bridge model configuration
    # ATTENTION: MUST BE DEFINED IN THE BRIDGE MODEL
    _group_model_field = ''
    _checkbox_model_field = ''
    _checkbox_fields_group_identifier = {}

    # Computed configuration
    _checkboxgroup_config = {}

    # ------------
    # BRIDGE MODEL
    # ------------
    @api.model
    def get_group(self, group_identifier):
        """Helper method to be used (or overloaded) in bridge models.
           Intended to be used in get_checkboxgroup_config()
        """
        # Get the group model
        group_model_field = getattr(self, self._group_model_field)
        group_model_name = group_model_field.comodel_name

        # HINT: By default the group_identifier is the 'sosync_fs_id'
        #       Override this method in the bridge model if an other identifier is given
        group = self.env[group_model_name].search([('sosync_fs_id', '=', group_identifier)])

        # Check that exactly none or one group was found
        assert len(group) < 2, "More than one Group found for sosync_fs_id %s" % group_identifier

        # Return the record set
        return group

    @api.model
    def get_checkboxgroup_config(self):
        # Compute self._checkboxgroup_config         
        if not self._checkboxgroup_config:
            
            config = {'group_model_field': getattr(self, self._group_model_field),
                      'checkbox_model_field': getattr(self, self._checkbox_model_field),
                      'fields_to_groups': {key: self.get_group(value) 
                                           for key, value in self._checkbox_fields_group_identifier.iteritems()}
                      }

            # TODO: Check that all field exists and that it is a boolean Field
            # assert isinstance(self._fields[cf], fields.Boolean), "Field missing or no boolean field %s.%s" \
            #                                                      "" % (self._name, cf)

            # Store the config into an instance attribute to avoid recomputation
            self._checkboxgroup_config = config
            
        return self._checkboxgroup_config

    @api.multi
    def get_checkbox_model_records(self):
        config = self.get_checkboxgroup_config()
        checkbox_model_records = self.mapped(config['checkbox_model_field'].name)
        return checkbox_model_records

    # CRUD
    @api.model
    def create(self, values, **kwargs):
        values = values or {}
        res = super(FRSTCheckboxBridgeModel, self).create(values, **kwargs)
        # Run group_to_checkbox() in the checkbox model
        if res:
            checkbox_model_records = res.get_checkbox_model_records()
            checkbox_model_records.group_to_checkbox()
        return res

    @api.model
    def write(self, values, **kwargs):
        values = values or {}
        res = super(FRSTCheckboxBridgeModel, self).create(values, **kwargs)
        # Run group_to_checkbox() in the checkbox model
        if res:
            checkbox_model_records = self.get_checkbox_model_records()
            checkbox_model_records.group_to_checkbox()
        return res

    @api.multi
    def unlink(self):
        # Get related records from checkboxmodel to update after the unlink
        checkbox_model_records = self.get_checkbox_model_records()

        # Unlink the records
        res = super(FRSTCheckboxBridgeModel, self).unlink()

        # Run group_to_checkbox() in the checkbox model based on the remaining groups after the unlink
        if res:
            checkbox_model_records.group_to_checkbox()

        return res
