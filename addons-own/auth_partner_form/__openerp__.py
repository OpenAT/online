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
    'name': "auth_partner_form",
    'summary': """Update/Create Partner Data with auth token""",
    'description': """

Set Partner Data with Token
===========================

New Controller:
"/meine-daten" or
"/meinedaten"

Example URL:
http://localhost:8010/meine-daten?fs_ptoken=123456789


ATTENTION: The token must be at least 6 chars long, is alphanumeric and case sensitive.
    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net",
    'category': 'Authentication',
    'version': '1.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'website',
        'fso_base',
        'fso_base_website',
        'fso_con_zmr',
        'auth_partner',
    ],
    'data': [
        'data/auth_partner_user_group.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/snippets.xml',
        #'views/fsonline_menu.xml', # Moved to fsonline addon
        'data/data.xml',
    ],
}
