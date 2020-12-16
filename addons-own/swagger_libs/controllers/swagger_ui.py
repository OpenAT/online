# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request

import validators
import datetime

from openerp.tools.mail import html_sanitize
import urllib


class SwaggerUIDist(http.Controller):
    @staticmethod
    def api_url_valid(api_url):
        return api_url.startswith(request.httprequest.host_url)\
               and validators.url(api_url)

    def raise_on_invalid_api_url(self, api_url):
        # Empty URL is valid
        if not api_url:
            return

        # Other URLs are checked
        if not self.api_url_valid(api_url):
            raise Exception("swagger_spec_url not allowed")

    @http.route(['/swagger-ui/index.html'], type="http", auth="user", website=True)
    def swagger_ui(self, swagger_spec_url=None):
        self.raise_on_invalid_api_url(swagger_spec_url)
        return request.render('swagger_libs.swagger_ui_index_html',
                              {'swagger_spec_url': swagger_spec_url}
                              )

    @http.route(['/swagger-editor/index.html'], type="http", auth="user", website=True)
    def swagger_editor(self, swagger_spec_url=None):
        self.raise_on_invalid_api_url(swagger_spec_url)
        return request.render('swagger_libs.swagger_editor_index_html',
                              {'swagger_spec_url': swagger_spec_url}
                              )
