# -*- coding: utf-8 -*-
from openerp.addons.fso_base.tools.validate import is_valid_url
from openerp.tools.translate import _
from jinja2 import Template, Environment, FileSystemLoader
import requests
from requests import Session
import os
import ntpath
import logging
# https://pypi.python.org/pypi/timeout-decorator
#import timeout_decorator

logger = logging.getLogger(__name__)


# Avoid exceptions on nested dict variables
# http://stackoverflow.com/questions/21692387/jinja2-exception-handling
# http://jinja.pocoo.org/docs/2.9/api/#writing-filters
def empty_if_exception_filter(value):
    try:
        return value
    except:
        return ""


class GenericTimeoutError(Exception):
    def __init__(self):
        Exception.__init__(self, "Execution stopped because of global timeout and not the request.Session() timeout!"
                                 "There may be a passphrase in your private key.")


def render_template(template="", **template_args):
    """
    Renders a file as a jinja2 template based on the **template_args

    :param template: template data or file system path to the template file
    :param template_args: arguments used in the template (dicts)
    :return: rendered template
    """
    # Try to detect if the template is a file or directly the jinja data to render
    if os.path.exists(template):
        j2_env = Environment(loader=FileSystemLoader(os.path.abspath(os.path.dirname(template))))
        j2_env.filters['empty_if_exception_filter'] = empty_if_exception_filter
        soap_request_template = j2_env.get_template(ntpath.basename(template))
        request_data = soap_request_template.render(**template_args)
    else:
        jinja2_template = Template(template)
        request_data = jinja2_template.render(**template_args)

    return request_data


# Multithreaded enabled timeout strategy
# ATTENTION: !!! It may be that timeout_decorator crashes python! At least it does on Mac OSX and there are hints
#                it also did it on linux !!!
#                TODO: We only used it here to prevent the case of a hung program if there
#                is a passphrase in the keys. So if we check for a passphrase we can be sure there will be no timeout
#                by that! requests has its own timeout so no problem there either!
#@timeout_decorator.timeout(18, use_signals=False, timeout_exception=GenericTimeoutError)
def soap_request(url="", template="", http_header={}, crt_pem="", prvkey_pem="", request_data=False, **template_args):

    # Check for missing or malformed parameters
    assert all((url, template or request_data)), _("Parameters missing! Required are url and template or request_data.")
    is_valid_url(url=url)

    # Check the certificates if set
    if crt_pem or prvkey_pem:
        assert all((crt_pem, prvkey_pem)), _("Certificate- and Private-Key-File needed if one of them is given!")
        assert len(crt_pem) <= 255 and len(prvkey_pem) <= 255, _("Path to cert- or key-file is longer than 255 chars!")
        assert os.path.exists(crt_pem), _("Certificate file not found at %s") % crt_pem
        assert os.path.exists(prvkey_pem), _("Private key file not found at %s") & prvkey_pem
        # TODO: Check if the key or cert do have a passphares and if raise an exception so we can remove the timeout
        #       decorator!

    # Set the http header of the request (not the soap header)
    http_header = http_header or {
        'content-type': 'text/xml; charset=utf-8',
        'SOAPAction': ''
    }

    # # Render the request data
    # # Try to detect if the template is a file or directly the jinja data to render
    # if os.path.exists(template):
    #     j2_env = Environment(loader=FileSystemLoader(os.path.abspath(os.path.dirname(template))))
    #     j2_env.filters['empty_if_exception_filter'] = empty_if_exception_filter
    #     soap_request_template = j2_env.get_template(ntpath.basename(template))
    #     request_data = soap_request_template.render(**template_args)
    # else:
    #     jinja2_template = Template(template)
    #     request_data = jinja2_template.render(**template_args)
    if request_data:
        assert not template, "Request Data and a Template set!"
    else:
        request_data = render_template(template=template, **template_args)

    # Create a Session Object (just like a regular UA e.g. Firefox or Chrome)
    session = Session()
    session.verify = True
    if crt_pem and prvkey_pem:
        session.cert = (crt_pem, prvkey_pem)

    # Send the request (POST)
    # http://docs.python-requests.org/en/master/user/advanced/
    request_data = request_data.encode('utf-8')
    response = session.post(url, data=request_data, headers=http_header, timeout=8)

    # Return the Response
    return response
