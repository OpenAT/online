# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.addons.fso_forms.controllers.controller import FsoForms
fso_forms_controller_obj = FsoForms()


# TODO: Edit on "fso_forms thank-you-page" should return to this controller
# TODO: Add public user access to the mailing list OR change the controller route
# TODO: Show some information about the list in the left box e.g.: goal and reached as well as name
# TODO: Test form warnings - if they show up?!?
# TODO: Approval Process for list subscriptions


class FSOSubscriptions(http.Controller):

    # Subscription Page
    @http.route(['/fso/subscription/<model("mail.mass_mailing.list"):mlist>'],
                type='http', auth="public", website=True)
    def mailing_list(self, mlist, **kwargs):

        # Use fso_forms to render the form for the mailing list page
        form_page = None
        form_page_html = ''
        if mlist and mlist.subscription_form:

            # Run the form controller first to check the data and create or update a record
            form_page = fso_forms_controller_obj.fso_form(form_id=mlist.subscription_form.id,
                                                          render_form_only=True, **kwargs)

            # Detect redirects
            if form_page and hasattr(form_page, 'location') and form_page.location:
                return form_page

            # Render the form page html code
            if form_page:
                form_page_html = form_page.render()

        # Lazy render the mailing list page
        mail_list_page = request.website.render('fso_subscriptions.subscription',
                                                {'kwargs': kwargs,
                                                 'form_page': form_page,
                                                 'form_html': form_page_html,
                                                 'mlist': mlist})
        return mail_list_page

    # TODO: Add a controller to unsubscribe from "email" Type Lists
    #       A User must be logged in!

