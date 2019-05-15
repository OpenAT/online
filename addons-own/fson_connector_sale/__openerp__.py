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
    'name': "FS-Online fso_con_sale",
    'summary': """FS-Online Webschnittstelle fuer website_sale_donate""",
    'description': """
FS-Online fso_con_sale
=========================

JSON Webschnittstelle die es erlaubt sale.order mit payment.transactions anzulegen.

Diese Schnittstelle ermoeglicht es folgende datensaetze in einem anzulegen
  - res.partner
  - res.partner fuer Firma
  - sale.order
  - sale.order.line
  - payment.transaction

TODO: 
-----
  - Neuer Payment Provider payment_fso_con_sale der für alle externen Zahlungen 
    (die nicht von uns durchgefuehrt werden sollen) zustaendig ist.
  - Korrekte Verarbeitung von odoo-Firmen in der sale.order im syncer v2 und im Fundraising Studio

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'website_sale_donate',
    ],
    'data': [
        'security/fson_connector_sale_groups.xml',
        'security/ir.model.access.csv',
        'views/fson_connector_sale.xml',
        'views/product_template.xml',
        'views/payment_acquirer.xml',
    ],
}
