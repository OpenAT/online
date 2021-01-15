# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "website_login_fs_ptoken",
    'summary': "website_login_fs_ptoken website (frontend) login form for fs_ptoken",
    'description': """
Token Login Form
----------------    
Provides a Login-Form for 'fs_ptoken' based on the website

This addon and the included login form can be used as a base for other website addons that need a frontend login form  
for fs_ptoken before accessing the page or resource.


Notes and Info
--------------
A token is a temporary password generated for odoo partners.

fs_ptoken stands for "Fundraising Studio Partner Token".
It says parnter-token and not user-token because tokens (res.partner.fstoken) are generated for partners and will
create an odoo user only at the first successful token usage by the addon auth_partner.

    """,
    "version": "8.0.1.0.0",
    "author": "Michael Karrer",
    "license": "AGPL-3",
    "category": "security",
    "depends": [
        'auth_partner',
        'fso_base_website',
    ],
    'data': [
        'templates/templates.xml',
    ],
    "installable": True,
}
