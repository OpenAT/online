# -*- coding: utf-8 -*-

from openerp.tools.translate import _
import openerp.addons.website_crm.controllers.main as main


class ContactUs(main.contactus):
    def create_lead(self, request, values, kwargs):

        # Add the default Website Sales Team
        website_sales_team = request.env.ref('website.salesteam_website_sales', raise_if_not_found=False)
        if website_sales_team:
            values['section_id'] = website_sales_team.id

        # Search for an existing res.partner
        existing_partner = False
        res_partner = request.env['res.partner'].sudo()
        if values.get('email_from', False):
            existing_partner = res_partner.search([('email', '=', values['email_from'])])
        if values.get('contact_name', False) and not existing_partner:
            existing_partner = res_partner.search([('name', 'ilike', values['contact_name'])])


        # Add existing res.partner
        if existing_partner and len(existing_partner) == 1:
            values['partner_id'] = existing_partner.id

        # Create the new lead
        lead_id = super(ContactUs, self).create_lead(request=request, values=values, kwargs=kwargs)
        if not lead_id:
            return lead_id

        # Post a message
        # HINT: We manually render the template cause send_message from email_template has a bug with the new API
        #       Therefore the language is always taken from the context and not like it is set in the template!
        #       This means that a user selecting en_us as the Website Language will get the en_US version of the
        #       template or de_DE if the website language is german when he submits the Contact Us Form.
        lead = request.env['crm.lead'].browse([lead_id])
        email_template = request.env['email.template'].sudo()
        template = request.env.ref('website_crm_extended.email_template_contact_us_request')
        rendered_template_body = email_template.render_template_batch(template=template.body_html,
                                                                      model='crm.lead',
                                                                      res_ids=[lead_id])[lead_id]
        lead.message_post(body=rendered_template_body,
                          subject=_("ContactUs-Form Request from %s") % lead.contact_name,
                          type='notification', subtype='mail.mt_comment')

        # Return result from super()
        return lead_id
