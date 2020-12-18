# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": """openapi_swagger_gui REST API/OpenAPI/Swagger GUI""",
    "summary": """openapi_swagger_gui add links to open the OpenAPI Spec File (OSF) in swagger-ui""",
    "category": "",
    "version": "8.0.1",
    "application": False,
    "author": "Michael Karrer",
    "license": "LGPL-3",
    "currency": "EUR",
    "depends": ["openapi", "swagger_libs"],
    "data": [
        "views/openapi_view.xml",
    ],
    "post_load": "post_load",
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "installable": True,
}
