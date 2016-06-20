# -*- coding: utf-8 -*-

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
    'name': 'fs_groups',
    'summary': "Fundrasing Studio Groups for product.product",
    'version': '8.0.2.1.0',
    "author": "Datadialog, Michael Karrer",
    "license": "AGPL-3",
    'maintainer': 'Datadialog',
    'category': 'Extra Tools',
    'website':
        'http://www.datadialog.net',
    'depends': ['website_sale_donate',
                'web_m2x_options',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'demo': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'images': []
}
