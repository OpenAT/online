# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "fso_forms_survey",
    'summary': """fso_forms_survey start survey after form submit""",
    'description': """
Start a survey after an successful form submit!
-----------------------------------------------
Select a survey that will be opened after an successful form submit!

The related survey.user_input record will be linked to the fso_form to know which set of answers is
related to this form.

This will also add a smart button to the fso_form form view to quickly open related survey results.

Logged in
---------
If the a user is logged in this user will be automatically used by the survey (survey.user_input). This alone
is already the default behaviour of the survey addon but this addon extends this by creating the survey.user_input 
record and linking it to the FS-Online form.

Not logged in but a res.partner form
------------------------------------
If the form targets the model res.partner this addon will create a survey.user_input with the newly created partner
if the user is not logged in. The survey will then be started with the token that is automatically set when creating
the survey.user_input record. This will link the survey to the res.partner even if no user is logged in.

Not logged in and not a res.partner form
----------------------------------------
In this case we do not know the partner and therefore can not link the survey to a res.partner record. But the
survey.user_input record is linked to the fson.form so at least we know which form was the origin of the survey answers.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net",
    'category': 'Website',
    'version': '1.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'fso_forms',
        'survey',
    ],
    'data': [
        'views/fson_form.xml',
        #'views/survey_user_input.xml',
    ],
}
