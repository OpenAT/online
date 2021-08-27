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
    'name': "website_sale_donate_google_tag_manager FS-Online Spendenshop Google Tag Manager Tracking",
    'version': '1.0',
    'summary': """Create events for the google tag manager enhanced ecommerce tracking""",
    'sequence': 200,
    'description': """

Create and send custom events for the google tag manager enhanced ecommerce tracking!
https://developers.google.com/tag-manager/enhanced-ecommerce
https://ga-dev-tools.web.app/enhanced-ecommerce/
https://chrome.google.com/webstore/detail/tag-assistant-legacy-by-g/kejbdjndbnbjgmefkgdddjlbokphdefk

Example shop from google showing the Universal Analytics (GTM) setup (GT4 and others are also shown here)
https://enhancedecommerce.appspot.com/checkout#customerInfo!GA-checkoutStep:uaGtm


https://www.analyticskiste.blog/analytics/ua-ga4-unterschiede-im-vergleich/#Aufgeklaert_Google_Analytics_4_8211_warum_4
https://www.analyticskiste.blog/analytics/gtag-js/

HINT: Some google tracking code is already prepared in the addon website_sale > website_sale_tracking.js but this seems 
      unfinished from odoo.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'depends': [
        #'fso_base_website',
        'website_sale_donate',
    ],
    'installable': True,
    'data': [
        'views/templates.xml',
    ],
}
