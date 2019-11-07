# -*- coding: utf-8 -*-
from openerp.addons.fso_forms.controllers.controller import FsoForms


class FsoFormsSubscriptions(FsoForms):

    def get_fso_form_records_by_user(self, form=None, user=None):
        records = super(FsoFormsSubscriptions, self).get_fso_form_records_by_user(form=form, user=user)

        # Only get records for correct form
        if records and form.model_id.model == 'mail.mass_mailing.contact':
            if len(form.mass_mailing_list_ids) == 1:
                records = records.filtered(lambda r: r.list_id.id == form.mass_mailing_list_ids.id)
            else:
                records = self.env['mail.mass_mailing.contact']

        return records

    # Make sure only records from the correct mailing list will be used for logged in users
    def get_fso_form_record(self, form):
        records = super(FsoFormsSubscriptions, self).get_fso_form_record(form)

        # Only get records for correct form
        if records and form.model_id.model == 'mail.mass_mailing.contact':
            if len(form.mass_mailing_list_ids) == 1:
                records = records.filtered(lambda r: r.list_id.id == form.mass_mailing_list_ids.id)
            else:
                records = self.env['mail.mass_mailing.contact']

            # Make sure the session is cleared in case of no record
            if not records:
                self.remove_fso_form_session_data(form.id)

        return records
