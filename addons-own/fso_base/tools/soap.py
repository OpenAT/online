# -*- coding: utf-8 -*-
from openerp.addons.fso_base.tools.validate import is_valid_url
from openerp.tools.translate import _
from jinja2 import Template
import requests
from requests import Session
from lxml import etree
import logging

logger = logging.getLogger(__name__)


def soap_request(url="", template="", http_header={}, crt_pem="", prvkey_pem="", **template_args):
    # Check soap request URL
    assert is_valid_url(url=url)[0], _('Soap Request URL %s not correct or DNS not found!') % url

    # Set the http header of the request (not the soap header)
    http_header = http_header or {
        'content-type': 'text/xml; charset=utf-8',
        'SOAPAction': ''
    }

    # Render the soap request data
    jinja2_template = Template(template)
    post_data = jinja2_template.render(**template_args)

    # Create a Session Object (just like a regular UA e.g. Firefox or Chrome)
    session = Session()
    session.verify = True
    session.cert = (crt_pem, prvkey_pem)

    # Send the request (POST)
    response = session.post(url, data=post_data, headers=http_header)

    # Parse the request response (XML EXPECTED!) for nice error reporting in next step
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        response_etree = etree.fromstring(response.content, parser=parser)
        response_string = etree.tostring(response_etree, pretty_print=True)
    except:
        response_string = response.content
        logger.warning(_('Soap request response returned non valid xml:\n%s\n') % response.content)

    # Check for response errors
    if response.status_code != requests.codes.ok:
        logger.error(_('Soap request returned the http error code %s') % response.status_code)
        logger.error(_('Soap request error response content:\n%s\n') % response_string)
        response.raise_for_status()

    return response.content
