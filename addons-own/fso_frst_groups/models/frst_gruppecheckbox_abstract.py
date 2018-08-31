# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTGruppeCheckbox(models.AbstractModel):
    _name = "frst.gruppecheckbox"

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

    # ------------
    # BRIDGE MODEL
    # ------------
    @api.multi
    def get_checkbox_model_records(self):
        # TODO
        # Must return a record set
        return

    @api.model
    def get_group(self, group_identifier):
        # HINT: By default the group_identifier is the 'sosync_fs_id'
        group = self.env['frst.zgruppedetail'].search([('sosync_fs_id', '=', group_identifier)])
        assert len(group) < 2, "More than one Group found for sosync_fs_id %s" % group_identifier
        return group

    @api.multi
    def group_to_checkbox(self, values):
        values = values or {}
        context = self.env.context or {}

        # Recursion switch
        if 'skipp_group_to_checkbox' in context:
            return

        return

    # CRUD
    @api.model
    def create(self, values, **kwargs):
        values = values or {}
        res = super(FRSTGruppeCheckbox, self).create(values, **kwargs)
        # Groups to checkboxes
        if res:
            res.group_to_checkbox(values)
        return res

    @api.model
    def write(self, values, **kwargs):
        values = values or {}
        res = super(FRSTGruppeCheckbox, self).create(values, **kwargs)
        # Groups to checkboxes
        if res:
            self.group_to_checkbox(values)
        return res

    @api.multi
    def unlink(self):
        # Get related records from checkboxmodel to update after the unlink
        checkbox_model_records = self.get_checkbox_model_records()

        # Unlink the records
        res = super(FRSTGruppeCheckbox, self).unlink()

        # Update checkbox fields of checkbox_model_records based on the remaining groups after the unlink
        if res:
            checkbox_model_records.group_to_checkbox()

        return res
