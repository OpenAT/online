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
    'name': "fso_gdpr",
    'summary': """fso_gdpr gdpr (dsgvo) extensions base""",
    'description': """

This addon will be the base for all extension regarding gdpr (dsgvo).

At the current stage this will only add the boolean field 'gdpr_accepted' to mail.mass_mailing.contact and res.partner

Info:
Die Allgemeine Datenschutz-Verordnung (General Data Protection Regulation GDPR) ist der neue rechtliche Rahmen der 
Europäischen Union, der festlegt, wie personenbezogene Daten gesammelt und verarbeitet werden dürfen. Die GDPR wird am 
25. Mai 2018 in Kraft treten. Sie gilt für alle Organisationen mit Sitz in der EU, die personenbezogene Daten 
verarbeiten und alle Organisationen weltweit, die Daten verarbeiten, die EU-Bürgern gehören.

Deshalb gilt die GDPR für Sie wenn Sie Digital Analytics verwenden um das Browsingverhalten von Endnutzern 
(Data Subjects / Betroffene) aus der Europäischen Union zu messen, unabhängig davon wo sich Ihr Unternehmen befindet. 
Sie müssen sich auf jeden Fall an die Vorgaben halten.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net",
    'category': 'GDPR',
    'version': '1.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'contacts',
        'mass_mailing',
    ],
    'data': [
        'views/res_partner.xml',
    ],
}
