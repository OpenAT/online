# -*- coding: utf-8 -*-

{
    'name': "FS-Online website_sale_categories_goals",
    'summary': """Allows specifying funding golas on a category.""",
    'description': """

website_sale_categories_goals
=============================
- add funding_goal to categories
- add funding_goal_percent to categories

    """,
    'author': "Datadialog",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'website_sale_categories',
    ],
    'installable': True,
    'data': [
        'views/product_public_category.xml'
    ],
}
