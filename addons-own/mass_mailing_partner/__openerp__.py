# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "mass_mailing_partner V2",
    "version": "8.0.2.1.0",
    "author": "Michael Karrer",
    "license": "AGPL-3",
    "category": "Marketing",
    "depends": [
        'mass_mailing',
        'fso_frst_personemail',
        'mass_mail_contact_firstname',
    ],
    'data': [
        'views/mail_mail_statistics_view.xml',
        'views/mail_mass_mailing_contact_view.xml',
        'views/mail_mass_mailing_view.xml',
        'views/res_partner_view.xml',
        'views/frst_personemail.xml',
        'wizard/partner_mail_list_wizard.xml',
    ],
    "installable": True,
}
