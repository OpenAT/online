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
    'name': "FS-Online website_language_fix",
    'summary': """website_language_fix, Copy field content to en_US with the frontend website editor""",
    'description': """

FS-Online website_language_fix
==============================

If a default language other than english is set for the website AND the english language is disabled then the data from 
the default language will also be written to the english (en_US) language for any database field edited with the 
website frontend editor.

This is useful if you want to empty (delete) a field in the frontend editor.
 
Without the fix one could not empty the field cause the english fallback was shown by odoo just like it is in the 
backend.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        'website',
    ],
    'data': [
    ],
}
