# -*- coding: utf-8 -*-
{
    'name': "fso_crm_extra_fields",

    'summary': """
        Add additional fields to crm.lead and use them for partner creation too""",

    'description': """
    """,

    'author': "DataDialog",
    'website': "https://www.datadialog.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Lead Automation',
    'version': '0.0.1',
    'license': 'AGPL-3',
    'depends': [
        'fso_base',
    ],
    'data': [
        'views/crm_lead.xml',
    ]
}
