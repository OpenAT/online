# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _inherit = "fson.form"

    mass_mailing_list_ids = fields.One2many(comodel_name="mail.mass_mailing.list",
                                            inverse_name="subscription_form",
                                            string="Mass Mailing List (FSO Subscription)")

    @api.constrains('mass_mailing_list_ids', 'field_ids')
    def contrains_mass_mailing_list_ids(self):
        for r in self:
            if len(r.mass_mailing_list_ids) > 1:
                raise ValidationError("You can only link one fso_subscription to this form")

            # Add additional checks for forms that are linked to fso_subscriptions (mail.mass_mailing.list)
            if len(r.mass_mailing_list_ids) == 1:
                mailing_list = r.mass_mailing_list_ids
                form_field_list_id = r.field_ids.filtered(lambda f: f.field_id.name == 'list_id')

                # Check the form model
                if r.model_id.model != 'mail.mass_mailing.contact':
                    raise ValidationError("Form model must be 'mail.mass_mailing.contact' if linked to a "
                                          "mass mailing list (mass_mailing_list_ids)!")

                # Check that the field 'list_id' exists in the form
                if len(form_field_list_id) != 1:
                    raise ValidationError("Field 'list_id' missing or used more than once!")

                # Check the default value of the list_id field to create contacts for the correct list
                if not form_field_list_id.default or mailing_list.id != int(form_field_list_id.default):
                    raise ValidationError("Default value of 'list_id' must match linked mailing list id")
