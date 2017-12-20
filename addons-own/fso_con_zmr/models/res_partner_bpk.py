# -*- coding: utf-8 -*-
from openerp import api, models, fields
import logging
import time
import datetime
from dateutil import parser as du_parser
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class ResPartnerBPK(models.Model):
    _name = 'res.partner.bpk'

    # ------
    # FIELDS
    # ------
    # res.company
    BPKRequestCompanyID = fields.Many2one(comodel_name='res.company', string="BPK Request Company",
                                          required=True, readonly=True)

    # res.partner
    BPKRequestPartnerID = fields.Many2one(comodel_name='res.partner', string="BPK Request Partner",
                                          required=True, readonly=True)

    # ATTENTION: Related fields are pretty slow expecially if no Full Vaccuum is done to the db regualarily
    #            Therefore this fields will also be updated by set_bpk_state()
    partner_state = fields.Char(string="Partner BPK State", readonly=True)

    # To make sorting the BPK requests easier
    LastBPKRequest = fields.Datetime(string="Last BPK Request", readonly=True)

    state = fields.Selection(selection=[('data_mismatch', 'Partner Data Mismatch'),
                                        ('found', 'Found'),
                                        ('error', 'Error')],
                             string="State", readonly=True)

    # Successful BPK request field set
    # --------------------------------
    # This set of fields gets only updated if private and public bpk was returned successfully
    BPKPrivate = fields.Char(string="BPK Private", readonly=True)
    BPKPublic = fields.Char(string="BPK Public", readonly=True)

    BPKRequestDate = fields.Datetime(string="BPK Request Date", readonly=True)
    BPKRequestURL = fields.Char(string="BPK Request URL", readonly=True)
    BPKRequestData = fields.Text(string="BPK Request Data", readonly=True)
    BPKRequestFirstname = fields.Char(string="BPK Request Firstname", readonly=True)
    BPKRequestLastname = fields.Char(string="BPK Request Lastname", readonly=True)
    BPKRequestBirthdate = fields.Date(string="BPK Request Birthdate", readonly=True)
    BPKRequestZIP = fields.Char(string="BPK Request ZIP", readonly=True)

    BPKResponseData = fields.Text(string="BPK Response Data", readonly=True)
    BPKResponseTime = fields.Float(string="BPK Response Time", readonly=True)

    BPKRequestVersion = fields.Integer(string="BPK Request Version", readonly=True)
    bpk_request_log = fields.Text(string="BPK Request Log", readonly=True)

    # Invalid BPK request field set
    # -----------------------------
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    BPKErrorCode = fields.Char(string="BPK-Error Code", readonly=True)
    BPKErrorText = fields.Text(string="BPK-Error Text", readonly=True)

    BPKErrorRequestDate = fields.Datetime(string="BPK-Error Request Date", readonly=True)
    BPKErrorRequestURL = fields.Char(string="BPK-Error Request URL", readonly=True)
    BPKErrorRequestData = fields.Text(string="BPK-Error Request Data", readonly=True)
    BPKErrorRequestFirstname = fields.Char(string="BPK-Error Request Firstname", readonly=True)
    BPKErrorRequestLastname = fields.Char(string="BPK-Error Request Lastname", readonly=True)
    BPKErrorRequestBirthdate = fields.Date(string="BPK-Error Request Birthdate", readonly=True)
    BPKErrorRequestZIP = fields.Char(string="BPK-Error Request ZIP", readonly=True)

    BPKErrorResponseData = fields.Text(string="BPK-Error Response Data", readonly=True)
    BPKErrorResponseTime = fields.Float(string="BPK-Error Response Time", readonly=True)

    BPKErrorRequestVersion = fields.Integer(string="BPK-Error Request Version", readonly=True)
    bpkerror_request_log = fields.Text(string="BPK-Error Request Log", readonly=True)

    # --------------
    # RECORD ACTIONS
    # --------------
    @api.multi
    def set_bpk_state(self):

        # Helper method to only write to the BPKs if values have changed
        # HINT: This comparison is less expensive than real writes to the db
        def write(bpk_request, values):
            # Add the current partner bpk state to the fields
            values['partner_state'] = bpk.BPKRequestPartnerID.bpk_state if bpk.BPKRequestPartnerID else False
            # Update the bpk if any value is changed
            if any(bpk_request[f] != values[f] for f in values):
                bpk_request.write(values)

        # ATTENTION: The order of the checks is very important e.g.: 'data check' must be made before 'found check'!
        # ATTENTION: Method used in create() and write() therefore ALWAYS use write() instead of '=' to prevent
        #            recurring write loops !!!
        for bpk in self:

            # 1.) Check if the partner data matches the bpk data
            if not bpk.BPKRequestPartnerID.all_bpk_requests_matches_partner_data(bpk_to_check=bpk):
                write(bpk, {'state': 'data_mismatch'})
                continue

            # 2.) Check if the bpk was found
            if bpk.BPKPublic and bpk.BPKRequestDate > bpk.BPKErrorRequestDate:
                write(bpk, {'state': 'found'})
                continue

            # 3.) Must be an error if state was not determined yet
            write(bpk, {'state': 'error'})
            continue

        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):

        # Create the BPK request in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but the BPK exits in the 'res' recordset already
        res = super(ResPartnerBPK, self).create(values)

        if res:
            res.set_bpk_state()

        return res

    @api.multi
    def write(self, values):

        # ATTENTION: !!! After this 'self' is changed (in memory i guess) 'res' is only a boolean !!!
        res = super(ResPartnerBPK, self).write(values)

        # Compute the bpk_state and bpk_error_code for the partner
        if res and self and 'state' not in values:
            self.set_bpk_state()

        return res

    # --------------
    # BUTTON ACTIONS
    # --------------
    # ATTENTION: Button Actions should not have anything else in the interface than 'self' because the mapping
    #            from old api to new api seems not correct for method calls from buttons if any additional positional
    #            or keyword arguments are used!
    # ATTENTION: Button actions must use the @api.multi decorator
    @api.multi
    def compute_state(self):
        self.set_bpk_state()
