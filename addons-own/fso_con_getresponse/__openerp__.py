# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
{
    "name": "fso_con_getresponse",
    "version": "8.0.1.0.0",
    "author": "Michael Karrer",
    "license": "AGPL-3",
    "category": "Connector",
    "summary": "Connector to GetResponse build with odoo oca connector framework",
    "depends": [
        'connector',
        'fso_frst_groups',
        'fso_frst_cds',
    ],
    "data": [
        'views/gr_custom_field.xml',
        'views/gr_tag.xml',
        'views/res_partner.xml',
        'views/getresponse_backend.xml',
        'views/frst_zgruppedetail.xml',
        'views/getresponse_frst_zgruppedetail.xml',
        'views/getresponse_gr_custom_field.xml',
        'views/getresponse_gr_tag.xml',
        'views/getresponse_frst_personemailgruppe.xml',
        'views/getresponse_menu.xml',
    ],
}
