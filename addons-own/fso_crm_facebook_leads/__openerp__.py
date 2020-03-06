# -*- coding: utf-8 -*-
{
    'name': "FSO CRM Facebook Leads (fso_crm_facebook_leads)",

    'summary': """
        Adds the fso menu and and additional fields specific to Fundraising Studio to crm_facebook_leads
    """,

    'description': """
Features:
    - FSO Menu entries
    - New crm.lead Fields for zGruppeDetail, firstname, lastname, and others by depending on 'fso_crm_extra_fields' 
      and 'crm_lead_firstname'
    - Automatically convert a Lead to an Opportunity to create an res.partner (Maybe controllable by a setting on the Form?)
      - Transfer zGruppeDetail(s) to the newly created res.partner

Features to be considered/discussed:
    - MAYBE TODO?: Wait with the lead to opportunity conversion until a Double-Opt-In E-Mail was sent and the Link was clicked?
    - MAYBE TODO?: Make it possible to select the CD's Folder in the leads form
    """,

    'author': "DataDialog",
    'website': "https://www.datadialog.net",
    'category': 'Lead Automation',
    'version': '0.0.1',
    'license': 'AGPL-3',
    'depends': [
        'crm_facebook_leads',
        'crm_lead_firstname',
        'fso_crm_extra_fields',
    ],
    'data': [
        'views/crm_facebook_form.xml',
        'views/fsonline_menu.xml',
    ]
}
