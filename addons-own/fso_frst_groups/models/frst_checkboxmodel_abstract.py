# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTCheckboxModel(models.AbstractModel):
    """
    ATTENTION: A Checkbox is only True if there are subscribed bridge model records and NO unsubscribed bm records!
    """
    _name = "frst.checkboxmodel"

    # List of all One2many fields pointing to bridge models
    # HINT: MUST BE DEFINED IN THE CHECKBOX MODEL!
    _bridge_model_fields = ()

    # Computed value containing all bridge models configurations
    _bridge_models_config = {}

    # --------------
    # CHECKBOX MODEL
    # --------------
    @api.model
    def get_bridge_models_config(self):
        # Compute self._bridge_models_config
        if not self._bridge_models_config:
            logger.info("Compute '_bridge_models_config' for checkbox model %s" % self.__class__.__name__)
            config = {}

            # Loop through bridge model fields
            for field in self._bridge_model_fields:
                bridge_model_field = self._fields.get(field)
                bridge_model_name = bridge_model_field.comodel_name

                # Get the config from the bridge model
                bridge_model_config = self.env[bridge_model_name].sudo().get_checkboxgroup_config()

                # Update '_bridge_models_config' with the config from the bridge model
                config[bridge_model_name] = {
                    'bridge_model_field': bridge_model_field,
                    'bridge_model_config': bridge_model_config,
                }

            # Store the config as a class attribute to avoid recomputation
            cls = self.__class__
            cls._bridge_models_config = config

        return self._bridge_models_config

    @api.multi
    def set_bm_group(self, group_id=None, bm_field='', bm_group_model_field='', bm_checkbox_model_field=''):
        group_id = int(group_id)

        # Loop through checkbox model records
        for r in self:

            # Get all bridge model records for this group (for the current checkbox model record)
            group_bm_records = r[bm_field].filtered(lambda bm: bm[bm_group_model_field].id == group_id)

            # Get bridge model records by bridge model state
            subscribed = group_bm_records.filtered(lambda g: g.state == 'subscribed')
            unsubscribed = group_bm_records.filtered(lambda g: g.state == 'unsubscribed')
            expired = group_bm_records.filtered(lambda g: g.state == 'expired')

            # Disable all unsubscribed bridge model records (and subscribe latest record if no subscribed records)
            # ---
            # HINT: A checkbox field is considered as True if there are no unsubscribed groups (see group_to_checkbox())
            if unsubscribed:

                # Subscribe newest unsubscribed bridge model record first if only unsubscribed records are found
                if not subscribed:
                    unsubscribed = unsubscribed.sorted(key=lambda k: k.write_date, reverse=True)
                    unsubscribed[0].sudo().with_context(skipp_group_to_checkbox=True).write(
                        {'steuerung_bit': False})
                    unsubscribed = unsubscribed - unsubscribed[0]

                # Expire all (remaining) unsubscribed bridge model records
                unsubscribed.sudo().with_context(skipp_group_to_checkbox=True).write(
                    {'gueltig_bis': fields.datetime.now() - timedelta(days=1)})

            # Enable newest expired bridge model record
            # ---
            elif not subscribed and expired:

                # Get newest expired bridge model record
                expired = expired.sorted(key=lambda k: k.write_date, reverse=True)
                expired = expired[0]

                # Compute gueltig_von and gueltig_bis
                gueltig_von = fields.datetime.strptime(expired.gueltig_von, DEFAULT_SERVER_DATE_FORMAT)
                if gueltig_von > fields.datetime.now():
                    gueltig_von = fields.datetime.now()
                gueltig_bis = fields.datetime.strptime(expired.gueltig_bis, DEFAULT_SERVER_DATE_FORMAT)
                if gueltig_bis < fields.datetime.now():
                    gueltig_bis = fields.date(2099, 12, 31)

                # Get newest expired bridge model record
                expired.sudo().with_context(skipp_group_to_checkbox=True).write(
                    {'gueltig_von': gueltig_von, 'gueltig_bis': gueltig_bis, })

            # Create a new bridge model record
            # ---
            elif not subscribed:
                # Create a new subscribed bridge model record for this group
                vals = {bm_checkbox_model_field: r.id,
                        bm_group_model_field: group_id,
                        'steuerung_bit': True,
                        'gueltig_von': fields.datetime.now(),
                        'gueltig_bis': fields.date(2099, 12, 31),
                        }
                group_bm_records.sudo().with_context(skipp_group_to_checkbox=True).create(vals)

        return True

    @api.multi
    def rem_bm_group(self, group_id=None, bm_field='', bm_group_model_field=''):
        group_id = int(group_id)

        # Loop through checkbox model records
        for r in self:
            # Get all bridge model records for this group for the current checkbox model record
            group_bm_records = r[bm_field].filtered(
                lambda bm: bm[bm_group_model_field].id == group_id)

            # Get bridge model records by bridge model state
            subscribed = group_bm_records.filtered(lambda g: g.state == 'subscribed')

            if subscribed:
                # Expire all subscribed bridge model records
                subscribed.sudo().with_context(skipp_group_to_checkbox=True).write(
                    {'gueltig_bis': fields.datetime.now() - timedelta(days=1)})

        return True

    @api.multi
    def checkbox_to_group(self, values=None):
        """ This method will create/subscribe or expire/unsubscribe all groups based on the checkbox fields.
            It can be used to restore all groups based on the checkbox values
            It is fired by the CRUD methods of the checkbox model
            If 'values' is not given it will update the groups for all checkbox fields
        """
        context = self.env.context or {}
        values = values or {}

        # Recursion switch
        if 'skipp_checkbox_to_group' in context:
            return True

        bridge_models_config = self.get_bridge_models_config()

        # Loop through bridge models
        for bridge_model, config in bridge_models_config.iteritems():
            bm_field = config['bridge_model_field']
            bm_config = config['bridge_model_config']
            bm_group_model_field = bm_config['group_model_field']
            bm_checkbox_model_field = bm_config['checkbox_model_field']

            # Process all checkbox fields if values is not given
            if values is None:
                checkbox_fields = {f: g for f, g in bm_config['fields_to_groups'].iteritems()}

            # Process only checkbox fields in values
            else:
                values = values or {}
                checkbox_fields = {f: g for f, g in bm_config['fields_to_groups'].iteritems() if f in values}

            # Continue to next bridge model if no fields are configured or in values
            if not checkbox_fields:
                continue

            # Loop through the checkbox model
            for r in self:

                # Loop through the checkbox fields
                for cf_name, group in checkbox_fields.iteritems():
                    if r[cf_name]:
                        r.set_bm_group(group_id=group.id,
                                       bm_field=bm_field.name,
                                       bm_group_model_field=bm_group_model_field.name,
                                       bm_checkbox_model_field=bm_checkbox_model_field.name)
                    else:
                        r.rem_bm_group(group_id=group.id,
                                       bm_field=bm_field.name,
                                       bm_group_model_field=bm_group_model_field.name)

        return True

    @api.multi
    def group_to_checkbox(self):
        """ This method will set or unset all checkboxes based on the current groups.
            It can be used to restore all checkbox values based on the groups
            It is fired by the CRUD methods of the bridge model
        """
        context = self.env.context or {}

        # Recursion switch to be used in inverse method 'checkbox_to_group'
        if 'skipp_group_to_checkbox' in context:
            return

        bridge_models_config = self.get_bridge_models_config()

        # Loop through checkbox model records
        for r in self:

            # Loop through bridge models
            for bridge_model_name, config in bridge_models_config.iteritems():
                bm_field = config['bridge_model_field']
                bm_config = config['bridge_model_config']
                bm_group_model_field = bm_config['group_model_field']

                # Loop through all groups mapped to a checkbox
                for checkbox_field_name, group in bm_config['fields_to_groups'].iteritems():
                    
                    # Get all bridge model records for this group for the current checkbox model record
                    group_bm_records = r[bm_field.name].filtered(
                        lambda bm: bm[bm_group_model_field.name].id == group.id)

                    # Get all subscribed bridge model records for this group for the current checkbox model record
                    subscribed = group_bm_records.filtered(lambda bm: bm.state == 'subscribed')

                    # Get all unsubscribed bridge model records for this group for the current checkbox model record
                    unsubscribed = group_bm_records.filtered(lambda bm: bm.state == 'unsubscribed')

                    # Check a group is not subscribed and unsubscribed through a bridge model record at the same time
                    if subscribed and unsubscribed:
                        logger.error("Group is subscribed and unsubscribed at the same time! "
                                     "bridge_model: %s, checkbox_model %s ID %s, group_id %s"
                                     "" % (bridge_model_name, r._name, r.id, group.id))
                    
                    # Compute the checkbox field value
                    value = True if subscribed and not unsubscribed else False

                    # Update the checkbox field value if needed
                    if value != r[checkbox_field_name]:
                        r.sudo().with_context(skipp_checkbox_to_group=True).write({checkbox_field_name: value})

        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(FRSTCheckboxModel, self).create(values)

        # Checkboxes to groups
        if 'skipp_checkbox_to_group' not in context:
            res.checkbox_to_group(values)

        return res

    @api.multi
    def write(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(FRSTCheckboxModel, self).write(values)

        # Checkboxes to groups
        if 'skipp_checkbox_to_group' not in context:
            self.checkbox_to_group(values)

        return res
