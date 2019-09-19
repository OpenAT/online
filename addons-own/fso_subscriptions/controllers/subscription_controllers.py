# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.addons.fso_forms.controllers.controller import FsoForms
fso_forms_controller_obj = FsoForms()

import requests


class FSOSubscriptions(http.Controller):

    # Subscription Page
    @http.route(['/fso/subscription/<model("mail.mass_mailing.list"):mlist>'],
                type='http', auth="public", website=True)
    def mailing_list(self, mlist, **kwargs):

        # Render the form html
        form_page = None
        form_page_html = ''
        if mlist and mlist.subscription_form:
            fso_forms_controller_obj = FsoForms()
            form_page = fso_forms_controller_obj.fso_form(form_id=mlist.subscription_form.id,
                                                          render_form_only=True, **kwargs)

            # Detect redirects
            if form_page and hasattr(form_page, 'location') and form_page.location:
                return form_page

        # TODO: Edit on "fso_forms thank-you-page" should return to this controller
        # TODO: Add a new class to hide some form fields e.g. hide_default
        #      (position: absolute, left: -10000, height 1px, width 1px, overflow hidden)
        # TODO: Auto create the corresponding fso_form related to the mailing list with all relevant settings
        #       - hidden field with form id (see class above)
        #       - form submit url
        #       - form thank you page url
        #       - mandatory fields
        # TODO: Add public user access to the mailing list OR change the controller route
        # TODO: Show some information about the list in the left box e.g.: goal and reached as well as name
        # TODO: Test form warnings - if they show up?!?
        form_page_html = form_page.render()
        mail_list_page = request.website.render('fso_subscriptions.subscription',
                                  {'kwargs': kwargs,
                                   'form_page': form_page,
                                   'form_html': form_page_html,
                                   'mlist': mlist})
        return mail_list_page

    # TODO: Add a controller to unsubscribe from "email" Type Lists
    #       A User must be logged in!

