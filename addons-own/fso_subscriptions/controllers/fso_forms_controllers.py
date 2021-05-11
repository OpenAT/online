# -*- coding: utf-8 -*-
from openerp.addons.fso_forms.controllers.controller import FsoForms
from openerp.http import request


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

    # Use the partner data to prefill the fso_form
    def _prepare_kwargs_for_form(self, form, record=None, **kwargs):
        kwargs = super(FsoFormsSubscriptions, self)._prepare_kwargs_for_form(form, record=record, **kwargs)

        # If this is not a request or a post request we do not populate data from public_user_partner
        if not request or not request.httprequest or request.httprequest.method == 'POST' or not request.website:
            return kwargs

        # If a record was found we do not need to populate form data from the public_user_partner
        if record:
            return kwargs

        # Find the partner of the request user is a user is logged in
        # ATTENTION: request.env.user MAY BE NULL BUT request.uid MAY BE SET ! ALWAYS USE request.uid !!!
        request_user_partner = None
        request_user = request.env['res.users'].sudo().browse([request.uid])
        if request_user and request.website.user_id and request_user.id != request.website.user_id.id:
            request_user_partner = request_user.partner_id

        # Populate the kwargs with data from the logged in website-user-partner
        if request_user_partner:
            kwargs.update({
                'email': request_user_partner.email,
                'firstname': request_user_partner.firstname,
                'lastname': request_user_partner.lastname,
                'gender': request_user_partner.gender,
                'anrede_individuell': request_user_partner.anrede_individuell,
                'title_web': request_user_partner.title_web,
                'birthdate_web': request_user_partner.birthdate_web,
                'phone': request_user_partner.phone,
                'mobile': request_user_partner.mobile,
                'street': request_user_partner.street,
                'street2': request_user_partner.street2,
                'street_number_web': request_user_partner.street_number_web,
                'zip': request_user_partner.zip,
                'city': request_user_partner.city,
                'state_id': request_user_partner.state_id.id,
                'country_id': request_user_partner.country_id.id,
            })

        return kwargs
