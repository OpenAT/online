# -*- coding: utf-8 -*-

{
    'name': 'fso_partner_appointed_date',
    'summary': '''FS-Online appointed date field.''',
    'description': '''
FS-Online appointed date
================================
Add appointed date field on res.partner to be used for special
dates in workflows.

Setting this field generates a mail.message with the date.

    ''',
    'author': 'Martin Kaip',
    'version': '0.1',
    'website': 'https://www.datadialog.net',
    'installable': True,
    'depends': [
        'fso_mail_message_subtypes_appointed_date',
    ],
    'data': [],
}