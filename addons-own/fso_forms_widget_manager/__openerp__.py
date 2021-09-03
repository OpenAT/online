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
    'name': "fso_forms_widget_manager",
    'summary': """fso_forms_widget_manager""",
    'description': """
    
Create and show widget manager entries related to an fso_form.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net",
    'category': 'Website',
    'version': '1.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'fso_forms',
        'website_widget_manager',
    ],
    'data': [
        'views/fson_form.xml',
    ],
}
