# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "mass_mailing_partner",
    "version": "8.0.2.1.0",
    "author": "Michael Karrer",
    "license": "AGPL-3",
    "category": "Marketing",
    "depends": [
        'mass_mailing',
        'fso_frst_personemail',
    ],
    # DISABLED BY MIKE:
    #"post_init_hook": "post_init_hook",
    'data': [
        'views/mail_mail_statistics_view.xml',
        'views/mail_mass_mailing_contact_view.xml',
        'views/mail_mass_mailing_view.xml',
        'views/res_partner_view.xml',
        'wizard/partner_mail_list_wizard.xml'
    ],
    "installable": True,
}
