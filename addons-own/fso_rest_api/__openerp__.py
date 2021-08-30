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
    'name': "FS-Online fso_rest_api",
    'summary': """FS-Online Rest API for Fundraising Studio""",
    'description': """
Create an openapi integration for the Fundraising Studio models and methods.

Includes a documentation based on restructured text and Sphinx

ATTENTION: !!! All changes to the 'frst' rest api integration will be removed on addon update !!!

If you need to make local or manual changes create a new integration!


    """,
    'author': "Datadialog - Michael Karrer, Martin Kaip",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.3.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'openapi_metrics',
        'openapi_swagger_gui',
        'fsonline',
    ],
    'data': [
        'data/run_on_install_update.xml',
        'data/frst_api_user_group.xml',
        'data/frst_rest_api.xml',
        'data/res_partner.xml',
        'data/frst_zverzeichnis.xml',
        'data/frst_zgruppe.xml',
        'data/frst_zgruppedetail.xml',
        'data/frst_persongruppe.xml',
        'data/frst_personemailgruppe.xml',
        'data/product_template.xml',
        'data/product_product.xml',
        'data/sale_order.xml',
        'data/sale_order_line.xml',
        'data/payment_transaction.xml',
        'data/payment_acquirer.xml',
        'data/res_country.xml',
        'data/res_currency.xml',
        'data/product_payment_interval.xml'
    ],
}
