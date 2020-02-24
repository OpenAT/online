# -*- coding: utf-8 -*-
import re
import validators
from email.utils import parseaddr
import socket
from urlparse import urlparse
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


class URLFormatError(Exception):
    pass


class URLDNSError(Exception):
    pass


def is_valid_url(url, dns_check=True):
    assert isinstance(url, (str, unicode)), _("URL must be a string!")

    # Check for a valid URL
    if not validators.url(url):
        raise URLFormatError(_('URL format is not valid: %s') % url)

    # Make a quick DNS check instead of a full HTTP GET request (because a request.get() can be really slow)
    if dns_check:
        try:
            socket.gethostbyname(urlparse(url).hostname)
        except Exception as e:
            raise URLDNSError(_('URL DNS check failed!\n%s\n%s\n') % (url, e))

    return True


def is_valid_email(email):
    """
    :param email: (str) email address in the format "Mike Test <mike@test.com>" or just "mike@test.com"
    :return: (boolean) True or False
    """
    # If a mako expression is in the e-mail skipp validation
    if "${" in email:
        return True

    # If a FRST print field expression is in the e-mail skipp validation
    frst_print_field_matcher = re.compile("\%.+\%")
    if bool(frst_print_field_matcher.match(email)):
        return True

    assert isinstance(email, (str, unicode)), _("E-Mail must be a string!")

    # TODO: Add MX and DNS Test option (could be done by library "flanker")

    return validators.email(parseaddr(email)[1]) is True
