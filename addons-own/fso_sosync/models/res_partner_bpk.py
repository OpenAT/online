# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner.bpk"
    _inherit = ["res.partner.bpk", "base.sosync"]

    # FIELDS
    # ------
    # NEW:
    state = fields.Selection(sosync="True")

    # res.company
    bpk_request_company_id = fields.Many2one(sosync="True")

    # res.partner
    bpk_request_partner_id = fields.Many2one(sosync="True")

    # To make sorting the BPK request easier
    last_bpk_request = fields.Datetime(sosync="True")

    # Make debugging of multiple request on error easier
    bpk_request_log = fields.Text(sosync="True")

    # Successful BPK request field set
    # --------------------------------
    # This set of fields gets only updated if private and public bpk was returned successfully
    bpk_private = fields.Char(sosync="True")
    bpk_public = fields.Char(sosync="True")

    bpk_request_date = fields.Datetime(sosync="True")
    bpk_request_url = fields.Char(sosync="True")
    bpk_request_data = fields.Text(sosync="True")
    bpk_request_firstname = fields.Char(sosync="True")
    bpk_request_lastname = fields.Char(sosync="True")
    bpk_request_birthdate = fields.Date(sosync="True")
    bpk_request_zip = fields.Char(sosync="True")

    bpk_response_data = fields.Text(sosync="True")
    bpk_response_time = fields.Float(sosync="True")

    # Invalid BPK request field set
    # -----------------------------
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    bpk_error_code = fields.Char(sosync="True")
    bpk_error_text = fields.Text(sosync="True")

    bpk_error_request_date = fields.Datetime(sosync="True")
    bpk_error_request_url = fields.Char(sosync="True")
    bpk_error_request_data = fields.Text(sosync="True")
    bpk_error_request_firstname = fields.Char(sosync="True")
    bpk_error_request_lastname = fields.Char(sosync="True")
    bpk_error_request_birthdate = fields.Date(sosync="True")
    bpk_error_request_zip = fields.Char(sosync="True")

    bpk_error_response_data = fields.Text(sosync="True")
    bpk_error_response_time = fields.Float(sosync="True")
