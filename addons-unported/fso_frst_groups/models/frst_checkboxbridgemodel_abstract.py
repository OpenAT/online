# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTCheckboxBridgeModel(models.AbstractModel):
    """
    USAGE:
        checkbox model:
            must inherit 'frst.checkboxmodel'
            '_bridge_model_fields' must be set

        bridge model:
            must inherit 'frst.gruppestate' FIRST and then 'frst.checkboxbridgemodel'
           _group_model_field, _checkbox_model_field and _checkbox_fields_group_identifier must be set

           Optional: alter get_group() if you use a different group_identifier than 'sosync_fs_id'

    ATTENTION: A Checkbox is 'Set/True' if there are subscribed bridge model records AND NO unsubscribed bm records!
    """
    _name = "frst.checkboxbridgemodel"

    # Bridge model configuration
    # ATTENTION: MUST BE DEFINED IN THE BRIDGE MODEL
    _group_model_field = ''
    # Not needed because we get it from _checkbox_model_field with rsplit('.')[0] for now (check set_bm_group())
    # _target_model_field = ''

    _checkbox_model_field = ''
    _checkbox_fields_group_identifier = {}

    # Computed configuration storage to avoid unneded recomputation
    # ATTENTION: Do not directly use self._checkboxgroup_config except in get_checkboxgroup_config()
    #            ALWAYS use 'self.get_checkboxgroup_config()' instead!
    _checkboxgroup_config = {}
    _checkboxgroup_config_date = False

    # ------------
    # BRIDGE MODEL
    # ------------
    @api.model
    def get_target_model_id_from_checkbox_record(self, checkbox_record=False):
        """ Override this in bridge models where the group_target_model is not the checkbox_model"""
        if checkbox_record:
            return checkbox_record.id
        else:
            return False

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
        bridge_model_name = self.__class__.__name__
        group_model_field = self._group_model_field
        checkbox_model_field = self._checkbox_model_field

        # Check if a recomputation of the configuration is needed
        recompute_needed = True if not self._checkboxgroup_config_date else False
        if self._checkboxgroup_config_date:
            group_model_name = self._fields.get(self._group_model_field).comodel_name
            group_model_obj = self.env[group_model_name]
            last_changed_group = group_model_obj.search([], order='write_date DESC', limit=1)
            if last_changed_group:
                last_changed_group_datetime = fields.datetime.strptime(last_changed_group.write_date,
                                                                       DEFAULT_SERVER_DATETIME_FORMAT)
                if last_changed_group_datetime >= self._checkboxgroup_config_date:
                    recompute_needed = True

        # Compute '_checkboxgroup_config'
        if recompute_needed or not self._checkboxgroup_config:
            logger.info("Compute '_checkboxgroup_config' for bridge model %s" % bridge_model_name)

            # TODO: Check that all chechbox model checkbox fields are existing and of type Bool
            # assert isinstance(self._fields[cf], fields.Boolean), ("Field missing or no boolean field %s.%s"
            #     "" % (self._name, cf))
            # TODO: Check that group_model_field and checkbox_model_field are of type Many2one

            # Get related groups for the checkbox fields
            # ATTENTION: Fields are only added if a group could be found
            fields_to_groups = {}
            for checkbox_field, group_identifier in self._checkbox_fields_group_identifier.iteritems():
                group = self.get_group(group_identifier)
                if group:
                    fields_to_groups[checkbox_field] = group
                else:
                    logger.error("Group not found for checkbox field '%s'! (%s)" % (checkbox_field, bridge_model_name))
            
            config = {'group_model_field': group_model_field,
                      'checkbox_model_field': checkbox_model_field,
                      'fields_to_groups': fields_to_groups
                      }

            # Store the config as a class attribute to avoid unneeded recomputation
            cls = self.__class__
            cls._checkboxgroup_config = config
            cls._checkboxgroup_config_date = fields.datetime.now()
            
        return self._checkboxgroup_config

    @api.multi
    def get_checkbox_model_records(self):
        config = self.get_checkboxgroup_config()
        # TODO: Check resolve of . notation of checkbox_model_field (e.g.: frst_personemail_id.partner_id)
        checkbox_model_records = self.mapped(config['checkbox_model_field'])
        return checkbox_model_records

    # CRUD
    @api.model
    def create(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(FRSTCheckboxBridgeModel, self).create(values)

        # Run group_to_checkbox() in the checkbox model
        if 'skipp_group_to_checkbox' not in context:
            checkbox_model_records = res.get_checkbox_model_records()
            checkbox_model_records.group_to_checkbox()

        return res

    @api.multi
    def write(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(FRSTCheckboxBridgeModel, self).write(values)

        # Run group_to_checkbox() in the checkbox model
        if 'skipp_group_to_checkbox' not in context:
            checkbox_model_records = self.get_checkbox_model_records()
            checkbox_model_records.group_to_checkbox()

        return res

    @api.multi
    def unlink(self):
        context = self.env.context or {}

        # Get checkbox model records before unlink
        if 'skipp_group_to_checkbox' not in context:
            # Get related records from checkboxmodel to update after the unlink
            checkbox_model_records = self.get_checkbox_model_records()

        # Unlink the records
        res = super(FRSTCheckboxBridgeModel, self).unlink()

        # Run group_to_checkbox() in the checkbox model based on the remaining groups after the unlink
        if 'skipp_group_to_checkbox' not in context:
            checkbox_model_records.group_to_checkbox()

        return res
