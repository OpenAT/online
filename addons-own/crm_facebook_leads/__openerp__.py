# -*- coding: utf-8 -*-
{
    'name': "CRM Facebook Leads",

    'summary': """
        Synchronize Facebook Leads with Odoo CRM Leads""",

    'description': """
    """,

    'author': "DataDialog",
    'website': "https://www.datadialog.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Lead Automation',
    'version': '0.0.1',
    'depends': [
        'crm',
        'utm',
    ],
    'data': [
        'data/crm_facebook_leads_fetch.xml',
        'security/group_crm_facebook_leads_manager.xml',
        'security/ir.model.access.csv',
        'views/crm_facebook_page.xml',
        'views/crm_facebook_form.xml',
        'views/crm_facebook_form_field.xml',
    ]
}
