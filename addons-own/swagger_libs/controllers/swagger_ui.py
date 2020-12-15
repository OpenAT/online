# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request

import datetime

from openerp.tools.mail import html_sanitize
import urllib


class SwaggerUIDist(http.Controller):

    @http.route(['/swagger-ui/index.html'], type="http", auth="user", website=True)
    def swagger_ui(self, swagger_spec_url="https://petstore.swagger.io/v2/swagger.json"):
        return request.render('swagger_libs.swagger_ui_index_html',
                              {'swagger_spec_url': swagger_spec_url}
                              )

    @http.route(['/swagger-editor/index.html'], type="http", auth="user", website=True)
    def swagger_editor(self, swagger_spec_url="https://petstore.swagger.io/v2/swagger.json"):
        return request.render('swagger_libs.swagger_editor_index_html',
                              {'swagger_spec_url': swagger_spec_url}
                              )
