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
    'name': "FS-Online: payment_fsotransfer",
    'summary': """payment_fsotransfer Payment Provider: Zahlschein oder Überweisung""",
    'description': """

Erlaubt es per Zahlschein oder Überwesung zu zahlen
===================================================

Payment Provider für (gedruckte/n) Zahlschein(e) oder Banküberweisung

Zahlschein Payment Provider für FS-Online
-------------------------------------------

ToDo: Hacken um die Zustellung der gedruckten Zahlscheine zu verhindern.

    """,
    'author': "DataDialog",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'fso_base_website',
        'payment',
        'website_sale_categories',
        'website_sale_donate',
    ],
    'installable': True,
    'data': [
        # Template has to be loaded first because fsotransfer_data.xml uses its id ;)
        'views/fsotransfer_acquirerbutton.xml',
        'data/fsotransfer_data.xml',
        'views/fsotransfer_transaction.xml',
    ],
}
