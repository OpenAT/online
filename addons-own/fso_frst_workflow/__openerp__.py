# -*- coding: utf-8 -*-
{
    'name': "fso_frst_workflow",

    'summary': """
        One way model to sync Fundraising Studio Workflows to FS-Online """,

    'description': """
    """,

    'author': "DataDialog",
    'website': "https://www.datadialog.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '0.0.1',
    'license': 'AGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'views/frst_workflow.xml',
    ]
}
