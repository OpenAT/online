# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from fso_forms_controllers import FsoFormsSubscriptions as FsoForms

# ATTENTION: This is dangerous because it will not include any inheritance of the FsoForms class next to or after
#            this addon - good enough for now...
forms_class_object = FsoForms()


class FSOSubscriptions(http.Controller):

    # Subscription Page
    @http.route(['/fso/subscription/<model("mail.mass_mailing.list"):mlist>'],
                type='http', auth="public", website=True)
    def mailing_list_subscription_page(self, mlist, **kwargs):

        # Redirect to the startpage of the website if not published or no fso_form is linked
        if not mlist or not mlist.website_published or not mlist.subscription_form:
            request.redirect('/')

        # Run the fso_forms controller first to check the data and create or update a record
        form_page = forms_class_object.fso_form(form_id=mlist.subscription_form.id,
                                                render_form_only=True, **kwargs)

        # Detect redirects from fso_forms
        if form_page and hasattr(form_page, 'location') and form_page.location:
            return form_page

        # Check if a website user is logged in
        user = request.env.user
        public_website_user = request.website.user_id
        website_partner = None
        if user and public_website_user and user.id != public_website_user.id:
            if not user.has_group('base.group_user'):
                website_partner = user.partner_id
        
        # Populate the kwargs with data from the logged in website-user-partner
        if website_partner and form_page and form_page.qcontext:
            if not form_page.qcontext.get('record') and not form_page.qcontext.get('kwargs'):
                form_page.qcontext['kwargs'].update({
                    'email': website_partner.email,
                    'firstname': website_partner.firstname,
                    'lastname': website_partner.lastname,
                    'gender': website_partner.gender,
                    'anrede_individuell': website_partner.anrede_individuell,
                    'title_web': website_partner.title_web,
                    'birthdate_web': website_partner.birthdate_web,
                    'phone': website_partner.phone,
                    'mobile': website_partner.mobile,
                    'street': website_partner.street,
                    'street2': website_partner.street2,
                    'street_number_web': website_partner.street_number_web,
                    'zip': website_partner.zip,
                    'city': website_partner.city,
                    'state_id': website_partner.state_id.id,
                    'country_id': website_partner.country_id.id,
                })

        # Render the fso_forms page html code
        form_page_html = form_page.render() if form_page else ''

        # Lazy render the mailing list subscription page
        mail_list_page = request.website.render('fso_subscriptions.subscription',
                                                {'kwargs': kwargs,
                                                 'form_page': form_page,
                                                 'form_html': form_page_html,
                                                 'mlist': mlist})
        return mail_list_page

    # TODO !!!
    @http.route(['/fso/subscription/manager'], type='http', auth="public", website=True)
    def subscription_manager(self, list_types=tuple(['email']), auto_unsubscribe_ids=None, **kwargs):

        user = request.env.user
        public_website_user = request.website.user_id

        # Check if a user is logged-in and if not redirect to the startpage of the website
        if user.id == public_website_user.id:
            return request.redirect("/")

        # TODO: set or remove subscription
            # TODO: auto_unsubscribe

        # Find all published mailing lists
        list_domain = [('website_published', '=', True)]
        if list_types:
            list_domain.append(('list_type', 'in', list_types))
        public_lists = request.env['mail.mass_mailing.list'].search(list_domain)
        if not public_lists:
            return request.redirect("/")
        public_lists_types = list(set(public_lists.mapped('list_type')))

        # Get subscribed published mailing lists for current user
        subscriptions = request.env['mail.mass_mailing.contact'].search([('partner_id', '=', user.id)])
        subscribed_lists = subscriptions.mapped('list_id') if subscriptions else request.env['mail.mass_mailing.list']
        subscribed_public_lists = subscribed_lists.filtered(
            lambda l: l for l in subscribed_lists if l in public_lists
        )

        return request.website.render('fso_subscriptions.subscription_manager',
                                      {'kwargs': kwargs,
                                       'public_lists': public_lists,
                                       'public_lists_types': public_lists_types,
                                       'subscribed_public_lists': subscribed_public_lists})
