# -*- coding: utf-8 -*-
import re
import validators
import socket
import urlparse
from openerp.tools.translate import _
import logging

logger = logging.getLogger(__name__)


def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        # strip exactly one dot from the right, if present
        hostname = hostname[:-1]
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def is_valid_url(url):
    assert isinstance(url, (str, unicode)), _("URL must be a string!")

    # Check for a valid URL
    if not validators.url(url):
        message = _('The URL is not valid! \nURL: %s\n\n'
                    'Please provide valid URL!\nE.g.: https://www.google.at/search?q=datadialog') % url
        warning = {'warning': {'title': _('Warning'), 'message': message}}
        return False, warning

    # Make a quick DNS check instead of a full HTTP GET request (because a request.get() can be really slow)
    try:
        socket.gethostbyname(urlparse(url).hostname)
    except Exception:
        message = _('DNS check failed for url %s!') % url
        warning = {'warning': {'title': _('Warning'), 'message': message}}
        return False, warning

    return True, {}

