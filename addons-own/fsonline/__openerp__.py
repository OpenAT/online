# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "FS-Online",
    'summary': """fs_online: addons, menu and users""",
    'description': """

FS-Online fso_base
==================
REPLACES: 
- base_config
- base_mod (add instance port to res.company)
- base_tools (image.py)

Module tasks:
-------------
- Install all other mandatory addons not already loaded by fso_base
- Create FS-Online custom menu and related views (e.g.: for donations)
- Create the sosync user (sosync) with full access to all models
- Create the sosyncer models (e.g.: for the sync table)
  - Create corresponding one2many field for the sync records in all synced models 
- Create the Fundraising Studio user (studio) with read only access to all models
- Create new FS-Online user_groups
  - fso_admin       (Full odoo access)
  - fso_readonly    (Full odoo access but only with read rights)
  - fso_manager     (Access to the FS-Online Menus and related models)
  - fso_user        (Access to the FS-Online Menus and restricted write access to some models)
- User Wizards
  - Donate product creation
    1. Type and Layout
    2. Settings
    3. SEO Url and LandingPage/Widget configuration
  - Donate product listing creation and update
    1. Root-Category (new/existing) and Settings
    2. Select Products

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.2',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        # Own Addons
        'fso_base',
        'fso_base_website',
        'website_sale_donate',
        'payment_frst',
        'payment_ogonedadi',
        'payment_postfinance',
        'auth_partner_form',
    ],
    'data': [
        'data/data_project.xml',
        'data/data_setup_css.xml',
        'data/data_sosync_user.xml',
        'security/ir.model.access.csv',
        'views/res_config.xml',
    ],
}
