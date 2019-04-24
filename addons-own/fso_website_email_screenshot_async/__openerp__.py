# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'FSON email editor screenshot generator',
    'summary': """
        Generate screenshots with connector async queue """,
    'version': '8.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Michael Karrer',
    'website': 'https://github.com/OCA/connector',
    'depends': [
        'connector',
        'fso_website_email',
    ],
    'data': [
    ],
    'demo': [
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
