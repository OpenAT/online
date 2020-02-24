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
    'name': "FS-Online website_domain_manager",
    'summary': """website_url_manager: URL Manager to set custom menu and footer or make redirects""",
    'description': """

website_domain_manager
======================
Use this URL Manager to set a custom website menu-template as well as a custom website footer-template by Domain.

**HINT:** Keep in mind that session cookies can be shared from parent domains to child (sub) domains but not the
other way around!

care.datadialog.net = Service Domain
spenden.care.at = Widget Domain
aktuell.care.at = Landing Page Domain

    """,
    'author': "Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'base', 'website',
    ],
    'installable': True,
    'data': [
        'security/group_website_domain_manager.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
}
