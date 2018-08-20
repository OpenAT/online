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
    'name': "FS-Online fso_website_email",
    'summary': """Website E-Mail Editor Extensions""",
    'description': """

FS-Online fso_website_email
===========================

Edit E-Mail templates through the website editor.

This addon includes new example snippets and basic E-Mail templates as well as extensions to the java front end 
editor and it's tools like the href edit pop-up window.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'website_mail',
        'fso_print_fields',
    ],
    'data': [
        'views/views.xml',
        #
        'views/email_editor.xml',
        'views/email_selection.xml',
        #
        'views/theme.xml',
        'views/snippets.xml',
        #
        'views/theme_default_snippets.xml',
        #
        'views/theme_dadi.xml',
        #
        'data/scheduled_actions.xml',
    ],
    'qweb': [
    ],
}
