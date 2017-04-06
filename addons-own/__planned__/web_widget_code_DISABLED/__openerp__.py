# -*- coding: utf-8 -*-
{
    'name': "Web Widget Code",

    'summary': """
Web widget 'code' implementation to be able to display and edit code with
syntax highlighting
""",

    'author': 'Management and Accounting Online',
    'license': 'LGPL-3',
    'website': 'https://maao.com.ua',

    'category': 'Technical Settings',
    'version': '8.0.0.0.2',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    'data': [
        'views/views.xml',
        'views/web_templates.xml',
    ],
}
