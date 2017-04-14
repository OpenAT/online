# -*- coding: utf-8 -*-
from openerp.addons.fso_base.tools.validate import is_valid_url
from openerp.tools.translate import _
from jinja2 import Template, Environment, FileSystemLoader
import requests
from requests import Session
import os
import ntpath
import logging

logger = logging.getLogger(__name__)


def soap_request(url="", template="", http_header={}, crt_pem="", prvkey_pem="", **template_args):
    # Validate the input
    assert all((url, template)), _("Parameters missing! Required are url and template.")
    assert is_valid_url(url=url)[0], _("Soap Request URL %s not valid and/or DNS resolution failed!") % url
    if crt_pem or prvkey_pem:
        assert all((crt_pem, prvkey_pem)), _("Certificate and private-key needed if one of them is given!")

    # Set the http header of the request (not the soap header)
    http_header = http_header or {
        'content-type': 'text/xml; charset=utf-8',
        'SOAPAction': ''
    }

    # Render the soap request data
    # Try to detect if the template is a file or directly the jinja data to render
    if os.path.exists(template):
        j2_env = Environment(loader=FileSystemLoader(os.path.abspath(os.path.dirname(template))))
        soap_request_template = j2_env.get_template(ntpath.basename(template))
        request_data = soap_request_template.render(**template_args)
    else:
        jinja2_template = Template(template)
        request_data = jinja2_template.render(**template_args)

    # Create a Session Object (just like a regular UA e.g. Firefox or Chrome)
    session = Session()
    session.verify = True
    if crt_pem and prvkey_pem:
        session.cert = (crt_pem, prvkey_pem)

    # Send the request (POST)
    # TODO: set some sort of timeout
    response = session.post(url, data=request_data, headers=http_header)

    # Check for response errors
    # DISABLED: Because in most cases one would still want to process the response content to check error in
    #           Soap XML Answer
    # if response.status_code != requests.codes.ok:
    #     logger.error(_('Soap request returned the http error code %s') % response.status_code)
    #     logger.error(_('Soap request response content:\n%s\n') % response.content)
    #     response.raise_for_status()

    # Return the Response
    # HINT: There could still be an error in the response.content: Not all are nice and raise an http error
    return response
