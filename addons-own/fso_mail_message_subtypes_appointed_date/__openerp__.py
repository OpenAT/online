# -*- coding: utf-8 -*-

{
    'name': 'fso_mail_message_subtypes_appointed_date',
    'summary': '''FS-Online mail message sub type for appointed date.''',
    'description': '''
FS-Online Instance Configuration
================================

Customer configuration for the instance wsca

- Default settings
- View modifications
- CSS
- Translations
    ''',
    'author': 'Martin Kaip',
    'version': '0.1',
    'website': 'https://www.datadialog.net',
    'installable': True,
    'depends': [
        'fso_mail_message_subtypes',
    ],
    'data': [
        'data/mail_message_subtypes.xml',
    ],
}