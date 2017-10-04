# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    'name': "FS-Online fso_base_website",
    'summary': """FS-Online fso_base_website""",
    'description': """
FS-Online fso_base_website
==========================
Basic addon for all FS-Online website related addons

## Load default Java Script libraries and css
Add java script libraries to assets_frontend:
- jquery.validate.js
    - additional-methods.js
    - methods_de.js
    - messages_de.js
    - additional-methods-fso.js
    - jquery-validate-defaults.js
- moment-with-locales.min.js

## robots.txt
Better default robots.txt view
- Update robots.txt view with better default settings and noupdate = 1
- Show robots.txt view arch field in website settings

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'fso_base',
        'website',
        #'website_domain_manager',
        #'website_widget_manager',
    ],
    'installable': True,
    'data': [
        'data/robots_txt.xml',
        'views/res_config.xml',
        'views/templates.xml',
        'views/website.xml',
        'views/fsonline_menu.xml',
    ],
}
