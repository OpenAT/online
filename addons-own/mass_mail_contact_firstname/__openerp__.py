# -*- coding: utf-8 -*-

#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Copyright (C)
#       2014:       Agile Business Group (<http://www.agilebg.com>)
#       2015:       Grupo ESOC <www.grupoesoc.es>
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

{
    'name': 'mass_mail_contact_firstname Mass Mail List Contact  first name and last name',
    'summary': "mass_mail_contact_firstname Split first name and last name for mass mail contacts",
    'version': '8.0.2.2.1',
    "author": "Camptocamp, "
              "Grupo ESOC Ingeniería de Servicios, "
              "ACSONE SA/NV, "
              "Odoo Community Association (OCA)"
              "Michael Karrer (Datadialog)",
    "license": "AGPL-3",
    'category': 'Extra Tools',
    'depends': ['base_setup',
                'mass_mailing'],
    'data': [
        'views/base_config_view.xml',
        'views/mail_mass_mailing_contact.xml',
        'data/mass_mail_list_contact.yml',
    ],
    'demo': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'images': []
}
