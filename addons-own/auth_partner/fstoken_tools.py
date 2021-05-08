# -*- coding: utf-8 -*-

from openerp import fields
from openerp.http import request
from openerp.tools.translate import _
import datetime
import time
# from openerp.addons.web.controllers.main import login_and_redirect, set_cookie_and_redirect

import logging
_logger = logging.getLogger(__name__)


def fstoken_sanitize(fs_ptoken):
    token = fs_ptoken
    errors = list()

    if not isinstance(token, basestring):
        errors.append(_('Your code is no string!'))
        return False, errors

    # Remove non alphanumeric characters
    token = ''.join(c for c in token.strip() if c.isalnum())

    # Check minimum token length
    if len(token) < 9:
        errors.append(_('Your code is too short!'))
        return False, errors

    # Return sanitized token-string and the empty error-messages-list
    return token, errors


def fstoken_check(fs_ptoken, log_usage=True):
    # Sanitize the token string
    token_record, errors = fstoken_sanitize(fs_ptoken)
    if errors:
        # Return empty token and some error message
        return False, False, errors

    # Check if the token record exists and is still valid
    token_record = request.env['res.partner.fstoken'].sudo().search([
        ('name', '=', token_record),
        ('expiration_date', '>=', fields.datetime.now())
    ])
    if not token_record:
        errors.append(_('Wrong or expired code!'))
        return False, False, errors

    # Check number of usages (max_checks)
    if token_record:
        # ATTENTION: Default to 10 if max_checks is not set or set to 0!
        max_checks = token_record.max_checks or 20
        if token_record.number_of_checks > max_checks:
            max_checks_msg = _('Token %s is expired because token was checked more than allowed by max_checks!'
                               '' % fs_ptoken)
            errors.append(max_checks_msg)
            _logger.info(max_checks_msg)
            return False, False, errors

    # Check if the token has a res.partner assigned
    partner = token_record.partner_id
    if not partner:
        errors.append(_('The code has no partner assigned!'))
        return False, False, errors

    # Two Factor Authentication
    if token_record and token_record.tfa_type or token_record.tfa_string:

        # Make sure both important tfa fields are filled
        if not token_record.tfa_type or not token_record.tfa_string:
            errors.append(_('Two Factor Authentication is enabled for the code but information is missing!'))
            return False, False, errors

        # tfa_type: approved_partner_email # TODO: Test this!!!
        if token_record.tfa_type == 'approved_partner_email':
            if token_record.tfa_string != token_record.partner_id.email:
                errors.append(_('Two Factor Authentication: The partner e-mail has changed!'))
                return False, False, errors
            if not token_record.partner_id.main_personemail_id:
                errors.append(_('Two Factor Authentication: The partner main email is missing!'))
                return False, False, errors
            if not token_record.partner_id.main_personemail_id.bestaetigt_am_um:
                errors.append(_('Two Factor Authentication: The partner main email is not approved!'))
                return False, False, errors

        # TODO: tfa_type: enter_string

    # Check/Create the res.user for the token
    user = token_record.partner_id.user_ids[0] if token_record.partner_id.user_ids else None

    # Append base.group_public to existing token website (public) user
    if user and not user.has_group('base.group_user') and not user.has_group('base.group_public'):
        _logger.info("Add user group base.group_public to user with id %s" % user.id)
        user.sudo().write({'groups_id': [(4, request.env.ref('base.group_public').id)]})

    # Create a new user
    if not user:
        # Create new User
        _logger.info('Create new res.user %s for valid fs_ptoken with id %s' % (partner.name, token_record.id))
        # HINT: Group Partner Manager is needed to update and use the own res.partner e.g. for sales orders or forms
        login = str(partner.id)
        if partner.email and not request.env['res.users'].sudo().search([('login', '=', partner.email)]):
            login = partner.email

        # ATTENTION: The new user is NOT added to the base.group_portal group because this will unlock the account
        #            menu in the website. However since the user does also not belong to base.group_user it should
        #            still be very easy to distinguish between internal and website user!
        # HINT: Add 'no_reset_password' to the context to avoid the auto signup-/passwort-reset-email from the addon
        #       auth_signup.
        user = request.env['res.users'].with_context(no_reset_password=True).sudo().create({
            'name': partner.name,
            'partner_id': partner.id,
            'email': partner.email,
            'login': login,
            'groups_id': [(6, 0, [request.env.ref('base.group_partner_manager').id,
                                  request.env.ref('base.group_public').id])],
        })
        # Directly commit changes to db in case of login right after this helper function so that the user is already
        # in the database and therefore available for all environments/caches of odoo.
        request.cr.commit()
        if not user:
            errors.append(_('The code has no user assigned!'))
            _logger.error('Could not create res.user %s for the fs_ptoken with id %s' % (partner.name,
                                                                                         token_record.id))
            return False, False, errors

    # Return fstoken record and the empty error-messages-list
    # ATTENTION: We pass the user on in case it was just created now and
    return token_record, user, errors


def log_token_usage(fs_ptoken, token_record, token_user, token_errors, httprequest):
    url = httprequest.url
    prefix = "fs_ptoken usage:"
    token_info = "fs_ptoken: '%s', token_record: '%s', token_user '%s', token_errors '%s', url: '%s'" \
                 "" % (fs_ptoken, token_record, token_user, token_errors, url)
    if token_errors:
        _logger.warning("%s ERROR %s" % (prefix, token_info))
    else:
        _logger.info("%s SUCCESS %s" % (prefix, token_info))


def store_token_usage(fs_ptoken, token_record, token_user, httprequest):
    token_log_obj = token_record.env['res.partner.fstoken.log'].sudo()
    token_log_obj.create({
        'log_date': datetime.datetime.now(),
        'fs_ptoken': fs_ptoken,
        'fs_ptoken_id': token_record.id,
        'user_id': token_user.id,
        'partner_id': token_user.partner_id.id,
        'url': httprequest.url,
        'ip': httprequest.remote_addr,
        'device': httprequest.user_agent,
    })
