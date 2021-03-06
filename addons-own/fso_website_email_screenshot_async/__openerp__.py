# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'FSON email editor screenshot generator',
    'summary': """
        Generate screenshots with connector async queue """,
    'description': """
    Render the screenshots async with the 'connector' addon! 
    """,
    'version': '8.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Michael Karrer',
    'website': 'https://github.com/OCA/connector',
    'depends': [
        #'connector',
        'connector_job_no_user',
        'fso_website_email',
    ],
    'data': [
        # Correct channel and function if needed
        'run_on_install_update.xml',
    ],
    'demo': [
    ],
    # Will run only after first install
    'post_init_hook': 'post_init_hook',
    # Run after uninstall
    'uninstall_hook': 'uninstall_hook',
}
