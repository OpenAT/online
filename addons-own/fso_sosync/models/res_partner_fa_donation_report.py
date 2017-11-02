# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner.fa_donation_report"
    _inherit = ["res.partner.fa_donation_report", "base.sosync"]

    # FIELDS
    # Donation Report FA (=Spendenmeldung fuer das Finanzamt Oesterreich)
    partner_id = fields.Many2one(sosync="True")
    bpk_company_id = fields.Many2one(sosync="True")
    anlage_am_um = fields.Datetime(sosync="True")
    ze_datum_von = fields.Datetime(sosync="True")
    ze_datum_bis = fields.Datetime(sosync="True")
    meldungs_jahr = fields.Integer(sosync="True")
    betrag = fields.Float(sosync="True")

    # Submission Information
    sub_datetime = fields.Datetime(sosync="True")
    sub_url = fields.Char(sosync="True")
    sub_typ = fields.Selection(sosync="True")
    #sub_data = fields.Char(string="Submission Data", readonly=True)
    #sub_response = fields.Char(string="Response", readonly=True)
    #sub_request_time = fields.Float(string="Request Time", readonly=True)
    #sub_log = fields.Text(string="Submission Log", readonly=True)

    # Submission BPK Information (Gathered at submission time from res.partner.bpk and copied here)
    sub_bpk_id = fields.Many2one(sosync="True")
    sub_bpk_company_name = fields.Char(sosync="True")
    sub_bpk_company_stammzahl = fields.Char(sosync="True")
    sub_bpk_private = fields.Char(sosync="True")
    sub_bpk_public = fields.Char(sosync="True")
    sub_bpk_firstname = fields.Char(sosync="True")
    sub_bpk_lastname = fields.Char(sosync="True")
    sub_bpk_birthdate = fields.Date(sosync="True")
    sub_bpk_zip = fields.Char(sosync="True")

    # Error Information
    error_code = fields.Char(sosync="True")
    error_text = fields.Char(sosync="True")

    # State Information
    skipped_by_id = fields.Many2one(sosync="True")
    skipped = fields.One2many(sosync="True")
    state = fields.Selection(sosync="True")
