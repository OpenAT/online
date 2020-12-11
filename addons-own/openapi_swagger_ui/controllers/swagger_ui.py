# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import urllib
import logging
import validators

from openerp import http
from openerp.http import request
from bs4 import BeautifulSoup


_logger = logging.getLogger(__name__)


class SwaggerUI(http.Controller):
    @staticmethod
    def html_replace_paths(doc, tag, att, path):
        for script in doc.findAll(tag):
            if script.get(att):
                if script[att].startswith('./'):
                    script[att] = path + script[att][1:]

    @staticmethod
    def html_replace_api_url(doc, from_url, to_url):
        for script in doc.findAll('script'):
            if 'SwaggerUIBundle(' in script.string:
                new_content = script.string.replace(
                    'url: "%s",' % from_url,
                    'url: "%s",' % to_url)
                script.string = new_content

    @staticmethod
    def html_add_custom_css(doc, css_file):
        link_tag = doc.new_tag('link')
        link_tag['rel'] = 'stylesheet'
        link_tag['type'] = 'text/css'
        link_tag['href'] = css_file
        doc.head.append(link_tag)

    @staticmethod
    def html_modify_document(doc, static_path, static_ui_path, api_url):
        SwaggerUI.html_replace_paths(
            doc=doc,
            tag='script',
            att='src',
            path=static_ui_path)

        SwaggerUI.html_replace_paths(
            doc=doc,
            tag='link',
            att='href',
            path=static_ui_path)

        SwaggerUI.html_add_custom_css(
            doc=doc,
            css_file=static_path + '/css/custom-ui.css')

        SwaggerUI.html_replace_api_url(
            doc=doc,
            from_url='https://petstore.swagger.io/v2/swagger.json',
            to_url=api_url)

    @staticmethod
    def api_url_allowed(host_url, url):
        # Local API URLs are always allowed
        if url.startswith(host_url):
            return True

        # Eventually add model to allow certain
        # external APIs
        return False

    @http.route(
        "/api/swagger-ui",
        type="http",
        auth="none",
        csrf=False,
        cors="*",
    )
    def index(self, **kwargs):
        api_url = kwargs.get('api')

        if not api_url:
            _logger.warning("Refusing, api parameter missing")
            return http.Response(
                'Parameter "api" missing.',
                400)

        if not validators.url(api_url):
            _logger.warning("Refusing, api is not a valid URL")
            return http.Response(
                'Parameter "api" must be a valid URL.',
                400)

        api_url_allowed = SwaggerUI.api_url_allowed(
            request.httprequest.host_url,
            api_url)

        if not api_url_allowed:
            _logger.warning("Refusing, URL in api is not allowed")
            return http.Response(
                'This API URL is not allowed.',
                400)

        static_path = '/openapi_swagger_ui/static/src'
        static_ui_path = static_path + '/swagger-ui-dist'

        index_url = request.httprequest.host_url[:-1] +\
            static_ui_path +\
            '/index.html'

        _logger.info("Reading and parsing %s" % index_url)
        index_raw = urllib.urlopen(index_url).read()
        document = BeautifulSoup(index_raw, "lxml")

        try:
            _logger.info("Modifying %s" % index_url)
            SwaggerUI.html_modify_document(
                doc=document,
                static_path=static_path,
                static_ui_path=static_ui_path,
                api_url=api_url)
        except Exception as ex:
            _logger.exception("Failed modifying Swagger UI index.html: %s" % ex.message)
            raise

        return str(document)
