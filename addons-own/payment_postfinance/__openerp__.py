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
    'name': "FS-Online Payment Provider: Postfinance ESR",
    'summary': """Payment Provider: Postfinance ESR (EinzahlungsSchein mit Referenznummer) Schweiz""",
    'description': """

Erlaubt es per ESR eine Dauerspende oder Einmalspende zu tätigen
================================================================

Dieses Addon erlaubt es per ESR eine Dauerspende oder Einmalspende mit FS-Online durchzuführen. Es ist ein
neuer Payment Provider für odoo der das addon payment als Basis nutzt.

Postfinanz ESR Payment Provider für FS-Online
---------------------------------------------

- Neuer odoo PaymentProvider für Postfinace ESR
- Generiert ESR Referenz Nummer auf Basis der Sales Order Nummer
- Gereriert ESR Kundennummer
- Generiert ESR Kodierzeile
- Neues Feld "Postfinance Kundennummer" (postfinance_customer_number) bei Bankkonten
- Überprüft ob die Währung mit der Postfinance Kundennummer übereinstimmt

    """,
    'author': "DataDialog - Michael Karrer (michael.karrer@datadialog.net)",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'fso_base',
        'fso_base_website',
        'payment',
    ],
    'installable': True,
    'data': [
        'views/postfinance_acquirerbutton.xml',
        'data/postfinance_data.xml',
        'views/postfinance_transaction.xml',
        'views/res_bank_partner.xml',
    ],
}
