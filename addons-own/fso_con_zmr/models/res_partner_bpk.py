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
    bpk_request_company_id = fields.Many2one(string="BPK Request Company",
                                             comodel_name='res.company', inverse_name="bpk_request_ids",
                                             required=True, readonly=True, oldname="BPKRequestCompanyID",
                                             index=True)

    # res.partner
    bpk_request_partner_id = fields.Many2one(string="BPK Request Partner",
                                             comodel_name='res.partner', inverse_name="bpk_request_ids",
                                             required=True, readonly=True, oldname="BPKRequestPartnerID",
                                             index=True)

    # ATTENTION: Related fields are pretty slow especially if no Full Vacuum is done to the db regularly
    #            Therefore this fields will also be updated by set_bpk_state()
    partner_state = fields.Char(string="Partner BPK State", readonly=True,
                                index=True)

    # To make sorting the BPK requests easier
    last_bpk_request = fields.Datetime(string="Last BPK Request", readonly=True)

    state = fields.Selection(selection=[('data_mismatch', 'Partner Data Mismatch'),
                                        ('found', 'Found'),
                                        ('error', 'Error')],
                             string="State", readonly=True)

    # Successful BPK request field set
    # --------------------------------
    # This set of fields gets only updated if private and public bpk was returned successfully
    bpk_private = fields.Char(string="BPK Private", readonly=True, oldname="BPKPrivate")
    bpk_public = fields.Char(string="BPK Public", readonly=True, oldname="BPKPublic")

    bpk_request_date = fields.Datetime(string="BPK Request Date", readonly=True, oldname="BPKRequestDate")
    bpk_request_url = fields.Char(string="BPK Request URL", readonly=True, oldname="BPKRequestURL")
    bpk_request_data = fields.Text(string="BPK Request Data", readonly=True, oldname="BPKRequestData")
    bpk_request_firstname = fields.Char(string="BPK Request Firstname", readonly=True, oldname="BPKRequestFirstname")
    bpk_request_lastname = fields.Char(string="BPK Request Lastname", readonly=True, oldname="BPKRequestLastname")
    bpk_request_birthdate = fields.Date(string="BPK Request Birthdate", readonly=True, oldname="BPKRequestBirthdate")
    bpk_request_zip = fields.Char(string="BPK Request ZIP", readonly=True, oldname="BPKRequestZIP")

    bpk_response_data = fields.Text(string="BPK Response Data", readonly=True, oldname="BPKResponseData")
    bpk_response_time = fields.Float(string="BPK Response Time", readonly=True, oldname="BPKResponseTime")

    bpk_request_version = fields.Integer(string="BPK Request Version", readonly=True, oldname="BPKRequestVersion")
    bpk_request_log = fields.Text(string="BPK Request Log", readonly=True)

    # Invalid BPK request field set
    # -----------------------------
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    bpk_error_code = fields.Char(string="BPK-Error Code", readonly=True, oldname="BPKErrorCode")
    bpk_error_text = fields.Text(string="BPK-Error Text", readonly=True, oldname="BPKErrorText")

    bpk_error_request_date = fields.Datetime(string="BPK-Error Request Date", readonly=True,
                                             oldname="BPKErrorRequestDate")
    bpk_error_request_url = fields.Char(string="BPK-Error Request URL", readonly=True, oldname="BPKErrorRequestURL")
    bpk_error_request_data = fields.Text(string="BPK-Error Request Data", readonly=True, oldname="BPKErrorRequestData")
    bpk_error_request_firstname = fields.Char(string="BPK-Error Request Firstname", readonly=True,
                                              oldname="BPKErrorRequestFirstname")
    bpk_error_request_lastname = fields.Char(string="BPK-Error Request Lastname", readonly=True,
                                             oldname="BPKErrorRequestLastname")
    bpk_error_request_birthdate = fields.Date(string="BPK-Error Request Birthdate", readonly=True,
                                              oldname="BPKErrorRequestBirthdate")
    bpk_error_request_zip = fields.Char(string="BPK-Error Request ZIP", readonly=True, oldname="BPKErrorRequestZIP")

    bpk_error_response_data = fields.Text(string="BPK-Error Response Data", readonly=True,
                                          oldname="BPKErrorResponseData")
    bpk_error_response_time = fields.Float(string="BPK-Error Response Time", readonly=True,
                                           oldname="BPKErrorResponseTime")

    bpk_error_request_version = fields.Integer(string="BPK-Error Request Version", readonly=True,
                                               oldname="BPKErrorRequestVersion")
    bpk_error_request_log = fields.Text(string="BPK-Error Request Log", readonly=True,
                                        oldname="bpkerror_request_log")

    # --------------
    # RECORD ACTIONS
    # --------------
    @api.multi
    def set_bpk_state(self):

        # Helper method to only write to the BPKs if values have changed
        # HINT: This comparison is less expensive than real writes to the db
        def write(bpk_request, values):
            # Add the current partner bpk state to the fields
            values['partner_state'] = bpk.bpk_request_partner_id.bpk_state if bpk.bpk_request_partner_id else False
            # Update the bpk if any value is changed
            if any(bpk_request[f] != values[f] for f in values):
                bpk_request.write(values)

        # ATTENTION: The order of the checks is very important e.g.: 'data check' must be made before 'found check'!
        # ATTENTION: Method used in create() and write() therefore ALWAYS use write() instead of '=' to prevent
        #            recurring write loops !!!
        for bpk in self:

            # 1.) Check if the partner data matches the bpk data
            if not bpk.bpk_request_partner_id.all_bpk_requests_matches_partner_data(bpk_to_check=bpk):
                write(bpk, {'state': 'data_mismatch'})
                continue

            # 2.) Check if the bpk was found
            if bpk.bpk_public and bpk.bpk_request_date > bpk.bpk_error_request_date:
                write(bpk, {'state': 'found'})
                continue

            # 3.) Must be an error if state was not determined yet
            write(bpk, {'state': 'error'})
            continue

        return True

    @api.multi
    def update_donation_reports(self):
        # Search if there are any donation reports to update
        for bpk in self:
            donation_reports = self.env['res.partner.donation_report']
            donation_reports = donation_reports.sudo().search(
                [('partner_id', '=', bpk.bpk_request_partner_id.id),
                 ('bpk_company_id', '=', bpk.bpk_request_company_id.id),
                 ('state', 'in', donation_reports._changes_allowed_states())])
            if donation_reports:
                # HINT: This will run update_state_and_submission_information()
                donation_reports.write({})

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):

        # Create the BPK request in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but the BPK exits in the 'res' recordset already
        res = super(ResPartnerBPK, self).create(values)

        if res:
            # Compute the state
            res.set_bpk_state()

            # Update donation reports
            res.update_donation_reports()

        return res

    @api.multi
    def write(self, values):

        # ATTENTION: !!! After this 'self' is changed (in memory i guess)
        #                'res' is only a boolean !!!
        res = super(ResPartnerBPK, self).write(values)

        # Compute the bpk_state and bpk_error_code for the partner
        if res and (not values or 'state' not in values):
            self.set_bpk_state()

        # Update donation reports on any bpk request state change
        if res:
            if 'state' in values or 'bpk_private' in values:
                self.update_donation_reports()

        return res

    @api.multi
    def unlink(self):

        partner = self.env['res.partner']
        for bpk in self:
            if bpk.bpk_request_partner_id:
                partner = partner | bpk.bpk_request_partner_id

        # HINT: 'res' is a boolean
        #       'self' still holds all the bpk requests after super is called BUT it is marked as deleted!!!
        res = super(ResPartnerBPK, self).unlink()

        # Update the partner bpk_state and therefore the donation-report state also!
        try:
            if res and partner:
                partner.sudo().write({'bpk_state': 'pending', 'bpk_request_needed': fields.datetime.now()})
        except Exception as e:
            logger.error("Could not set bpk_state for partner to pending at bpk-request unlink!")
            pass

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
