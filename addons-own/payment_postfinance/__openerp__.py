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
    'name': "FS-Online PayemntProvider Postfinance ESR",
    'summary': """Payment Provider: ESR (EinzahlungsSchein mit Referenznummer) Schweiz""",
    'description': """

Erlaubt es per ESR eine Dauerspende oder Einmalspende zu tätigen
================================================================

Dieses Addon erlaubt es per ESR eine Dauerspende oder Einmalspende mit FS-Online durchzuführen. Es ist ein
neuer Payment Provider für odoo der auch das addon payment als Basis nutzt.

Postfinanze ESR Payment Provider für FS-Online
----------------------------------------------

- Neuer odoo PaymentProvider für Postfinace ESR
- Generiert ESR Nummer
- Neues Feld für die Postfinance Kundennummer bei res.company
- Speichert ESR Nummer in der Payment Transaction

    """,
    'author': "DataDialog - Michael Karrer (michael.karrer@datadialog.net)",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'website_tools',
        'payment',
        'website_sale_payment_fix',
    ],
    'installable': True,
    'data': [
        # Template has to be loaded first because frst_data uses its id ;)
        'views/postfinance_acquirerbutton.xml',
        'data/postfinance_data.xml',
        'views/postfinance_transaction.xml',
    ],
}
