# -*- coding: utf-8 -*-

from openerp.tools.translate import _
import openerp.addons.website_crm.controllers.main as main
from openerp import http
from openerp.http import request
import logging

_logger = logging.getLogger(__name__)


class ContactUs(main.contactus):
    def create_lead(self, req, values, kwargs):

        # Add the default Website Sales Team
        website_sales_team = req.env.ref('website.salesteam_website_sales', raise_if_not_found=False)
        if website_sales_team:
            values['section_id'] = website_sales_team.id

        # Search for an existing res.partner
        existing_partner = False
        res_partner = req.env['res.partner'].sudo()
        if values.get('email_from', False):
            existing_partner = res_partner.search([('email', '=', values['email_from'])])
        if values.get('contact_name', False) and not existing_partner:
            existing_partner = res_partner.search([('name', 'ilike', values['contact_name'])])


        # Add existing res.partner
        if existing_partner and len(existing_partner) == 1:
            values['partner_id'] = existing_partner.id

        # Create the new lead
        lead_id = super(ContactUs, self).create_lead(request=req, values=values, kwargs=kwargs)
        if not lead_id:
            return lead_id

        # Post a message
        # HINT: We manually render the template cause send_message from email_template has a bug with the new API
        #       Therefore the language is always taken from the context and not like it is set in the template!
        #       This means that a user selecting en_us as the Website Language will get the en_US version of the
        #       template or de_DE if the website language is german when he submits the Contact Us Form.
        lead = req.env['crm.lead'].sudo().browse([lead_id])
        email_template = req.env['email.template'].sudo()
        # HINT: req.env.ref() will not work for with sudo() therefore we need to browse for the template again
        template_id = req.env.ref('website_crm_extended.email_template_contact_us_request').id
        template = req.env['email.template'].sudo().browse([template_id])
        rendered_template_body = email_template.render_template_batch(template=template.body_html,
                                                                      model='crm.lead',
                                                                      res_ids=[lead_id])[lead_id]
        lead.message_post(body=rendered_template_body,
                          subject=_("ContactUs-Form Request from %s") % lead.contact_name,
                          type='notification', subtype='mail.mt_comment')

        # Return result from super()
        return lead_id

    @http.route()
    def contact(self, **kwargs):
        # Check honeypot
        if kwargs.get('surname') or kwargs.get('hpfdadi'):
            _logger.warning("SPAM: Contact Us form: Honeypot fields are filled! \n%s\n" % str(kwargs))
            # Return empty form
            return request.website.render("website.contactus", {})

        # Clean kwargs from honeypot fields
        kwargs = {k: kwargs[k] for k in kwargs if k not in ['surname', 'surname_x', 'hpfdadi']}

        # Call the original controller
        page = super(ContactUs, self).contact(**kwargs)

        # Add countries and states to qcontext
        countries = request.env['res.country']
        countries = countries.sudo().search([])
        states = request.env['res.country.state']
        states = states.sudo().search([])
        if hasattr(page, 'qcontext'):
            page.qcontext.update({'countries': countries, 'states': states})

        return page

    @http.route()
    def contactus(self, **kwargs):
        # Check honeypot
        if kwargs.get('surname') or kwargs.get('hpfdadi'):
            _logger.warning("SPAM: Contact Us form: Honeypot fields are filled! \n%s\n" % str(kwargs))
            # Clear all values and go on
            kwargs = dict()
        else:
            # Clean kwargs from honeypot fields
            kwargs = {k: kwargs[k] for k in kwargs if k not in ['surname', 'surname_x', 'hpfdadi']}

        # Call the original controller
        page = super(ContactUs, self).contactus(**kwargs)

        # Add countries and states to qcontext
        countries = request.env['res.country']
        countries = countries.sudo().search([])
        states = request.env['res.country.state']
        states = states.sudo().search([])
        if hasattr(page, 'qcontext'):
            page.qcontext.update({'countries': countries, 'states': states})

        return page
