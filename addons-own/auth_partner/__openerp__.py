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
    'name': "FS-Online auth_partner",
    'summary': """Set res.partner by fs_ptoken""",
    'description': """

Set Partner in Session by Token
===============================

Use the parameter fs_ptoken to set the res.user for the current session.

If a valid token is found it will stay valid until:
    - the session is deleted
    - an other token is used
    - or a user logs in

The fs_ptoken is currently used in:
 - website_sale_donate and
 - auth_partner_form.

EXAMPLES:

Simple-Checkout-Product-Link with fs_ptoken attribute:
http://localhost:8010/shop/simple_checkout/einmalige-spende-6?fs_ptoken=123456789

ATTENTION: The token must be at least 6 chars long and alphanumeric.
WARNING: The value of fs_ptoken is case sensitive!


FSTOKEN TOOLS FOR PROGRAMMERS:

from openerp.addons.auth_partner.fstoken_tools import fstoken
partner, messages_token, warnings_token, errors_token = fstoken(fs_ptoken=kwargs.get('fsptoken', False))

# HINT: You could use fstoken() without the fs_ptoken kwarg to check any valid token in the current session.


    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net",
    'category': 'Authentication',
    'version': '1.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'web',
    ],
    'data': [
        'security/fs_token_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/res_partner_fstoken_log.xml',
    ],
}
