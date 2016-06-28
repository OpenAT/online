# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    'name': 'website_popup',
    'summary': '''
Displays a PopUp Box on every page of the website until the user closes it. Can be used for promotional banners,
to collect newsletter subscriptions and things alike.
''',
    'version': '8.0.1.0.0',
    'category': 'Website',
    'author': "Datadialog, Michael Karrer",
    'website': 'http://www.datadialog.net',
    'license': 'AGPL-3',
    'depends': [
        'website',
    ],
    'data': [
        'views/templates.xml',
        'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
