# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner.bpk"
    _inherit = ["res.partner.bpk", "base.sosync"]

    _sync_job_priority = 2000
    
    # HINT: FS-Online only model! Do not create or edit records in Fundraising Studio!

    # FIELDS
    # ------
    # NEW:
    state = fields.Selection(sosync="fson-to-frst")

    # res.company
    bpk_request_company_id = fields.Many2one(sosync="fson-to-frst")

    # res.partner
    bpk_request_partner_id = fields.Many2one(sosync="fson-to-frst")

    # To make sorting the BPK request easier
    last_bpk_request = fields.Datetime(sosync="fson-to-frst")

    # Make debugging of multiple request on error easier
    bpk_request_log = fields.Text(sosync="fson-to-frst")

    # Successful BPK request field set
    # --------------------------------
    # This set of fields gets only updated if private and public bpk was returned successfully
    bpk_private = fields.Char(sosync="fson-to-frst")
    bpk_public = fields.Char(sosync="fson-to-frst")

    bpk_request_date = fields.Datetime(sosync="fson-to-frst")
    bpk_request_url = fields.Char(sosync="fson-to-frst")
    bpk_request_data = fields.Text(sosync="fson-to-frst")
    bpk_request_firstname = fields.Char(sosync="fson-to-frst")
    bpk_request_lastname = fields.Char(sosync="fson-to-frst")
    bpk_request_birthdate = fields.Date(sosync="fson-to-frst")
    bpk_request_zip = fields.Char(sosync="fson-to-frst")
    bpk_request_street = fields.Char(sosync="fson-to-frst")


    bpk_response_data = fields.Text(sosync="fson-to-frst")
    bpk_response_time = fields.Float(sosync="fson-to-frst")

    # Invalid BPK request field set
    # -----------------------------
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    bpk_error_code = fields.Char(sosync="fson-to-frst")
    bpk_error_text = fields.Text(sosync="fson-to-frst")

    bpk_error_request_date = fields.Datetime(sosync="fson-to-frst")
    bpk_error_request_url = fields.Char(sosync="fson-to-frst")
    bpk_error_request_data = fields.Text(sosync="fson-to-frst")
    bpk_error_request_firstname = fields.Char(sosync="fson-to-frst")
    bpk_error_request_lastname = fields.Char(sosync="fson-to-frst")
    bpk_error_request_birthdate = fields.Date(sosync="fson-to-frst")
    bpk_error_request_zip = fields.Char(sosync="fson-to-frst")
    bpk_error_request_street = fields.Char(sosync="fson-to-frst")

    bpk_error_response_data = fields.Text(sosync="fson-to-frst")
    bpk_error_response_time = fields.Float(sosync="fson-to-frst")
