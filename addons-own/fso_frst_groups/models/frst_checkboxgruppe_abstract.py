# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTCheckboxGruppe(models.AbstractModel):
    _name = "frst.checkboxgruppe"

    _frst_gruppecheckbox_config = {
        'frst.persongruppe': {
            'bridge_model': 'frst.persongruppe',
            'bridge_model_checkbox_model_field': 'partner_id',
            'bridge_model_group_field': 'zgruppedetail_id',
            'bridge_model_group_model': 'frst.zgruppedetail',
            'checkbox_model_bridge_model_field': 'persongruppe_ids',
            'checkbox_fields': {
                'donation_deduction_optout_web': 110493,
                'donation_deduction_disabled': 128782,
                'donation_receipt_web': 20168,
            }
        },
        'frst.personemailgruppe': {
            'bridge_model': 'frst.personemailgruppe',
            'bridge_model_checkbox_model_field': 'partner_id',
            'bridge_model_group_field': 'zgruppedetail_id',
            'bridge_model_group_model': 'frst.zgruppedetail',
            'checkbox_model_bridge_model_field': 'main_personemail_id.personemailgruppe_ids',
            'checkbox_fields': {
                'donation_deduction_optout_web': 110493,
                'donation_deduction_disabled': 128782,
                'donation_receipt_web': 20168,
            }
        }

    }

    # --------------
    # CHECKBOX MODEL
    # --------------
    @api.model
    def get_bridge_models(self):
        all_models = self.env['ir.models'].search([])
        for model in all_models:
            if hasattr(model, '_inherit'):
                print model
        return True

    @api.multi
    def set_group(self, bridge_model, group_identifier):
        bridge_model_obj = self.env[bridge_model]
        group = bridge_model_obj.get_group(group_identifier)
        if not group:
            logger.error('Group not found %s %s' % (bridge_model, group_identifier))
            return False

        # TODO
        return True

    @api.multi
    def rem_group(self, bridge_model, group_identifier):
        # TODO
        return True

    @api.multi
    def checkbox_to_group(self, values):
        values = values or {}
        context = self.env.context or {}

        # Recursion switch
        if 'skipp_checkbox_to_group' in context:
            return True

        # Loop through bridge models
        bridge_models = self.get_bridge_models()

        for bridge_model in self._frst_gruppecheckbox_config:
            config = self._frst_gruppecheckbox_config[bridge_model]
            checkbox_fields = config['checkbox_fields']

            # Only execute if checkbox_fields of the bridge_model are in the values
            changed_fields = {k: v for k, v in checkbox_fields.iteritems() if k in values}
            if not changed_fields:
                continue

            # Set/Unset the group for the checkbox field
            for cf, group_identifier in changed_fields.iteritems():
                # Check that field exists and that it is a boolean Field
                assert isinstance(self._fields[cf], fields.Boolean), "Field missing or no boolean field %s.%s" \
                                                                     "" % (self._name, cf)

                # Set/Create or Expire/Unsubscribe the group based on the checkbox value for all records
                if values[cf]:
                    self.set_group(bridge_model, group_identifier)
                else:
                    self.rem_group(bridge_model, group_identifier)

        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values, **kwargs):
        values = values or {}
        res = super(FRSTCheckboxGruppe, self).create(values, **kwargs)
        # Checkboxes to groups
        if res:
            res.checkbox_to_group(values)
        return res

    @api.model
    def write(self, values, **kwargs):
        values = values or {}
        res = super(FRSTCheckboxGruppe, self).create(values, **kwargs)
        # Checkboxes to groups
        if res:
            self.checkbox_to_group(values)
        return res
