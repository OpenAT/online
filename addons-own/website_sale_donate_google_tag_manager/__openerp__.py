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
    'name': "website_sale_donate_google_tag_manager FS-Online Spendenshop Google Tag Manager tracking",
    'version': '1.0',
    'summary': """Create events for the google tag manager enhanced ecommerce tracking""",
    'sequence': 200,
    'description': """

Create and send custom events for the google tag manager enhanced ecommerce tracking!
https://developers.google.com/tag-manager/enhanced-ecommerce

HINT: Some google tracking code is already prepared in the addon website_sale > website_sale_tracking.js

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'depends': [
        'website_sale_donate',
    ],
    'installable': True,
    'data': [
        '/views/templates.xml',
    ],
}
