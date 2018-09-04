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
        group_model_field = self._fields.get(self._group_model_field)
        group_model_name = group_model_field.comodel_name

        group_model_obj = self.env[group_model_name]

        # Check if the model has 'sosync_fs_id' field
        # HINT: By default the group_identifier is the 'sosync_fs_id'
        #       Override this method in the bridge model if an other identifier is given
        if not hasattr(group_model_obj, 'sosync_fs_id'):
            return group_model_obj

        group = group_model_obj.search([('sosync_fs_id', '=', group_identifier)])

        # Check that exactly none or one group was found
        assert len(group) < 2, "More than one Group found for sosync_fs_id %s" % group_identifier

        return group


    @api.model
    def get_checkboxgroup_config(self):
        # Compute self._checkboxgroup_config
        if not self._checkboxgroup_config:
            bridge_model_name = self.__class__.__name__
            logger.info("Compute '_checkboxgroup_config' for bridge model %s" % bridge_model_name)

            # TODO: Check that all field exists and that they are boolean fields
            # assert isinstance(self._fields[cf], fields.Boolean), "Field missing or no boolean field %s.%s" \
            #                                                      "" % (self._name, cf)

            # Get related groups for the checkbox fields
            # ATTENTION: Fields are only added if a group could be found
            ftg = {}
            for checkbox_field, group_identifier in self._checkbox_fields_group_identifier.iteritems():
                group = self.get_group(group_identifier)
                if group:
                    ftg[checkbox_field] = group
                else:
                    logger.error("Group not found for checkbox field '%s'! (%s)" % (checkbox_field, bridge_model_name))
            
            config = {'group_model_field': self._fields.get(self._group_model_field),
                      'checkbox_model_field': self._fields.get(self._checkbox_model_field),
                      'fields_to_groups': ftg
                      }

            # Store the config as a class attribute to avoid recomputation
            cls = self.__class__
            cls._checkboxgroup_config = config
            
        return self._checkboxgroup_config

    @api.multi
    def get_checkbox_model_records(self):
        config = self.get_checkboxgroup_config()
        checkbox_model_records = self.mapped(config['checkbox_model_field'].name) # TODO
        return checkbox_model_records

    # CRUD
    @api.model
    def create(self, values):
        values = values or {}
        res = super(FRSTCheckboxBridgeModel, self).create(values)
        # Run group_to_checkbox() in the checkbox model
        if res:
            checkbox_model_records = res.get_checkbox_model_records()
            checkbox_model_records.group_to_checkbox()
        return res

    @api.multi
    def write(self, values):
        values = values or {}
        res = super(FRSTCheckboxBridgeModel, self).write(values)
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
