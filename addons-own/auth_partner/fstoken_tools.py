# -*- coding: utf-8 -*-

from openerp import fields
from openerp.http import request
from openerp.tools.translate import _
import datetime
import time


# fstoken cases:
# ==============
# HINT: if the token is in the session it will not show up in anywhere since we just return the partner but not
#       the token fstoken()
#
#
# 1.) No fs_ptoken, logged in user:
# No Messages
# res.partner from the res.users
#
# 2.) Wrong fs_ptoken, logged in user:
# error_token = "Your token is wrong but you are already logged in."
# res.partner des res.users
#
# 3.) Valid fs_ptoken, logged in user, same res.partner
# messages_token =  "Valid Token"
# res.partner from the res.users
#
# 4.) Valid fs_ptoken, logged in user, same res.partner
# warnings_token "Valid token but different from logged in user! Please log off to use the token"
# res.partner from the res.users
#
#
# 5.) No fs_ptoken
# No Messages
# No Partner
#
# 6.) Wrong fs_ptoken
# error_token = "Wrong token."
# res.partner from the res.users
#
# 7.) Valid fs_ptoken
# messages_token =  "Valid Token"
# res.partner from the res.users
#
def fstoken(fs_ptoken=None):
    token = fs_ptoken or request.session.get('valid_fstoken', None)
    token_record = None

    # Prepare return variables
    partner = None
    messages_token = list()
    warnings_token = list()
    errors_token = list()

    # Check and sanitize token format
    if token and isinstance(token, basestring):
        # Sanitize fs_ptoken (remove non alpha numeric characters like spaces or dashes)
        token = ''.join(c.upper() for c in token.strip() if c.isalnum())
        # Check for minimum fs_ptoken length
        if len(token) < 6:
            errors_token.append(_('Your code is too short!'))
    elif token:
        errors_token.append(_('Your code is no string!'))

    # TOKEN CHECK: Check token validity and find related res.partner
    if token and not errors_token:
        fstoken_obj = request.env['res.partner.fstoken']
        token_record = fstoken_obj.sudo().search([('name', '=', token)], limit=1)
        if token_record and fields.Datetime.from_string(token_record.expiration_date) >= fields.datetime.now():
            # Valid token with related res.partner
            if token_record.partner_id:
                partner = token_record.partner_id
                message = request.website.apf_token_success_message or _('Your code is valid!')
                messages_token.append(message)
            # Error: Valid token but res.partner is missing
            else:
                errors_token.append(_('The code was valid but the partner is missing!'))
        # Error: Wrong or expired token
        else:
            message = request.website.apf_token_error_message or _('Wrong or expired code!')
            errors_token.append(message)

    # USER CHECK: Check if a user is logged in and if use the res.partner of the logged in user
    if request.uid != request.website.user_id.id:
        user_obj = request.env['res.users']
        user = user_obj.sudo().browse([request.uid])
        assert user.partner_id, _('You are logged in but your user has no res.partner assigned!')
        # Check if a fstoken res.partner was found but is different than the res.partner of the logged in user
        # HINT: We do not append this warning if the token comes from a valid_fstoken in the session!
        if fs_ptoken and partner and partner.id != user.partner_id.id:
            warnings_token.append(_('You are logged in but your user does not match the partner of the given code!\n'
                                    'Please log out if you want to use this code!'))
        # Use the partner of the logged in user
        partner = user.partner_id

    # VALID TOKEN:
    # Update session and statistic
    if not errors_token and token:
        # Write sanitized token to the current session for subsequent use
        request.session['valid_fstoken'] = token
        # Update "last_date_of_use" field of "res.partner.fstoken"
        token_record.sudo().write({'last_date_of_use': fields.datetime.now()})
        # TODO: Log any valid fs_ptoken use to the "res.partner.fstoken.usage" model
    # WRONG TOKEN:
    elif errors_token and token:
        # Remove ANY valid token from the session
        request.session.pop('valid_fstoken', None)
        # Subsequent wrong token given for this session
        if request.session.get('wrong_fstoken_date'):
            # Reset if last incorrect try is older than 1h
            if datetime.datetime.now() > request.session['wrong_fstoken_date'] + datetime.timedelta(hours=1):
                request.session['wrong_fstoken_date'] = datetime.datetime.now()
                request.session['wrong_fstoken_tries'] = 1
            else:
                # SECURITY: Add a delay on subsequent wrong token tries to prevent simple brute force attacks
                # TODO: wrong_fstoken_tries >= 30: cancel connection to prevent a lot of open connections
                if request.session['wrong_fstoken_tries'] > 5:
                    time.sleep(4)
                request.session['wrong_fstoken_tries'] += 1
        # First time a wrong token was given for this session
        else:
            request.session['wrong_fstoken_date'] = datetime.datetime.now()
            request.session['wrong_fstoken_tries'] = 1
            # TODO: Log the first wrong token try of this session to the "res.partner.fstoken.usage" model
            #       We may not log any wrong attempt but just the first one because of brute force attacks?

    # Return the partner and the messages, warnings and errors
    return partner, messages_token, warnings_token, errors_token
