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
    'name': "FS-Online website_widget_manager",
    'summary': """Widget Manager: Generates the widget-embed-code, redirects to target page and checks widget status""",
    'description': """

website_widget_manager
======================

- Generates the widget-embed-code
- Redirects to the target page if the widget page is called directly
- Checks widget status
- Holds the custom iframe-resizer java script library

iframe-resizer script extensions
--------------------------------
The iframe resizer script has been extended by Samo Lajtinger from Abaton 
to make it possible to load custom source urls by HOST-URL parameters.

- The iframe "src" parameter can be overwritten by a HOST-URL parameter if it matches the iframe id
  e.g.: https://www.care.at/spenden/pakete-mit-zukunft/?ifcare1=%2Fpage%2Fcontactus%3Ftest%3Dno
  will load the page ".../page/contactus?test=no" into <iframe id="ifcare1" src="http://test.com/shop">
  instead of the original page "/shop"
- HOST-URL parameters will be passed to all managed iframe src urls
  e.g.: https://www.care.at/spenden/pakete-mit-zukunft/?load=ok&ifcare1=%2Fpage%2Fcontactus%3Ftest%3Dno
  will load the page ".../page/contactus?test=no&load=ok" into <iframe id="ifcare1" src="http://test.com/shop">
  The parameter "load=ok" is added to all ALL managed iframe src urls!

https://github.com/davidjbradshaw/iframe-resizer
Please look at the example html file at website_as_widget/test_iframe.html

    """,
    'author': "Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.2',
    'depends': [
        'base', 'website', 'website_domain_manager', 'web_tree_image',
    ],
    'installable': True,
    'data': [
        'security/group_website_widget_manager.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
}
