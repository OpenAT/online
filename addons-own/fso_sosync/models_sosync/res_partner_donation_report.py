# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerDonationReportSosync(models.Model):
    _name = "res.partner.donation_report"
    _inherit = ["res.partner.donation_report", "base.sosync"]

    _sync_job_priority = 3000

    info = fields.Text(sosync="True")
    imported = fields.Boolean(sosync="True")                        # Mark "imported" e.g.: for initial data acquisition

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
    state = fields.Selection(sosync="True")                 # ATTENTION: state may be written by FRST for "imported" Donation Reports
    error_type = fields.Selection(sosync="fson-to-frst")
    error_code = fields.Char(sosync="fson-to-frst")
    error_detail = fields.Text(sosync="fson-to-frst")
    submission_type = fields.Selection(sosync="fson-to-frst")
    submission_refnr = fields.Char(sosync="fson-to-frst")
    submission_firstname = fields.Char(sosync="fson-to-frst")
    submission_lastname = fields.Char(sosync="fson-to-frst")
    submission_birthdate_web = fields.Date(sosync="fson-to-frst")
    submission_zip = fields.Char(sosync="fson-to-frst")
    submission_bpk_request_id = fields.Char(sosync="fson-to-frst")
    submission_bpk_public = fields.Char(sosync="fson-to-frst")
    submission_bpk_private = fields.Char(sosync="fson-to-frst")

    # Fields from the Spendenmeldung-Meldung
    # --------------------------------------
    submission_id_datetime = fields.Datetime(sosync="fson-to-frst")     # Datetime of the submission (try) to FinanzOnline

    # Fields set after response from FinanzOnline
    # -------------------------------------------
    response_content = fields.Text(sosync="fson-to-frst")
    response_error_code = fields.Char(sosync="fson-to-frst")
    response_error_detail = fields.Text(sosync="fson-to-frst")
    response_error_orig_refnr = fields.Char(sosync="fson-to-frst")      # ERR-U-008 unbek. RefNr.

    # Allow Changes to the sosync fields even after the donation report was submitted
    def _changes_allowed_fields_after_submission(self):
        allowed_fields = super(ResPartnerDonationReportSosync, self)._changes_allowed_fields_after_submission()
        allowed_fields += self._sosyncer_fields
        return allowed_fields
