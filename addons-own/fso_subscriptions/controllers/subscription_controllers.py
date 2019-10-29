# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.addons.fso_forms.controllers.controller import FsoForms
fso_forms_controller_obj = FsoForms()


# TODO: Approval Process for list subscriptions


class FSOSubscriptions(http.Controller):

    # Subscription Page
    @http.route(['/fso/subscription/<model("mail.mass_mailing.list"):mlist>'],
                type='http', auth="public", website=True)
    def mailing_list_subscription_page(self, mlist, **kwargs):

        # Redirect to the startpage of the website if not published or no fso_form is linked
        if not mlist or not mlist.website_published or not mlist.subscription_form:
            request.redirect('/')

        # Run the fso_forms controller first to check the data and create or update a record
        form_page = fso_forms_controller_obj.fso_form(form_id=mlist.subscription_form.id,
                                                      render_form_only=True, **kwargs)

        # Detect redirects from fso_forms
        if form_page and hasattr(form_page, 'location') and form_page.location:
            return form_page

        # Render the fso_forms page html code
        form_page_html = form_page.render() if form_page else ''

        # Lazy render the mailing list subscription page
        mail_list_page = request.website.render('fso_subscriptions.subscription',
                                                {'kwargs': kwargs,
                                                 'form_page': form_page,
                                                 'form_html': form_page_html,
                                                 'mlist': mlist})
        return mail_list_page

    @http.route(['/fso/subscription/manager'], type='http', auth="public", website=True)
    def subscription_manager(self, list_types=tuple(['email']), auto_unsubscribe_ids=None, **kwargs):

        user = request.env.user
        public_website_user = request.website.user_id

        # Check if a user is logged and if not redirect to the startpage of the website
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
