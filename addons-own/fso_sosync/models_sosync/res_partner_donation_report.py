# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerDonationReportSosync(models.Model):
    _name = "res.partner.donation_report"
    _inherit = ["res.partner.donation_report", "base.sosync"]

    info = fields.Text(sosync="True")

    # Fields set by FRST at donation report creation
    # ----------------------------------------------
    submission_env = fields.Selection(sosync="True")
    partner_id = fields.Many2one(sosync="True")
    bpk_company_id = fields.Many2one(sosync="True")
    anlage_am_um = fields.Datetime(sosync="True")
    ze_datum_von = fields.Datetime(sosync="True")
    ze_datum_bis = fields.Datetime(sosync="True")
    meldungs_jahr = fields.Selection(sosync="True")
    betrag = fields.Float(sosync="True")
    cancellation_for_bpk_private = fields.Char(sosync="True")

    # Fields for state and submission (calculated and updated by FSON)
    # ----------------------------------------------------------------
    # ATTENTION: The 'error' state is only for errors prior to any submission!!! e.g.: bpk_missing
    state = fields.Selection(sosync="True")
    error_type = fields.Selection(sosync="True")
    error_code = fields.Char(sosync="True")
    error_detail = fields.Text(sosync="True")
    submission_type = fields.Selection(sosync="True")
    submission_refnr = fields.Char(sosync="True")
    submission_firstname = fields.Char(sosync="True")
    submission_lastname = fields.Char(sosync="True")
    submission_birthdate_web = fields.Date(sosync="True")
    submission_zip = fields.Char(sosync="True")
    submission_bpk_request_id = fields.Char(sosync="True")
    submission_bpk_public = fields.Char(sosync="True")
    submission_bpk_private = fields.Char(sosync="True")

    # Fields from the Spendenmeldung-Meldung
    # --------------------------------------
    submission_id_datetime = fields.Datetime(sosync="True")     # Datetime of the submission (try) to FinanzOnline

    # Fields set after response from FinanzOnline
    # -------------------------------------------
    response_content = fields.Text(sosync="True")
    response_error_code = fields.Char(sosync="True")
    response_error_detail = fields.Text(sosync="True")
    response_error_orig_refnr = fields.Char(sosync="True")      # ERR-U-008 unbek. RefNr.
