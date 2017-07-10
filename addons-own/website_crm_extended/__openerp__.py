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
    'name': "website_crm_extended",
    'summary': """Website Contact Form Extensions""",
    'description': """
website_crm_extended
====================
Extensions to the website contact form and the leads created by it.

- Add a frontend option to make the Company Name (partner_name) an optional field in the Form if enabled 
- Add website sales team to the new lead
- Add existing res.partner to the new lead
- Post a new chatter message based on an e-mail Template (normally send to the sales team members)
  HINT: Normally the e-mail will NOT be send to the res.partner because the default
  setting is "Do not add as follower automatically"

ATTENTION
=========
If you use the addon **website_snippet_contact_form** you must disable the Company Name (partner_name) as a 
mandatory field for the drag and drop snippet of the *contact form* also!
Look at the customer-addon of the pfot instance to see how it is done!

    """,
    'author': "Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'website',
        'website_crm',
    ],
    'data': [
        'data/email_templates.xml',
        'views/templates.xml',
    ],
    'installable': True,
}
