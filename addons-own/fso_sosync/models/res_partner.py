# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "base.sosync"]

    # TODO: dbo.Person relation model

    # ACTIVE (= Hidden)
    active = fields.Boolean(sosync="True")          # Record verstecken

    # RELATED FIELDS
    parent_id = fields.Many2one(sosync="True")
    state_id = fields.Many2one(sosync="True")
    country_id = fields.Many2one(sosync="True")
    gender = fields.Selection(sosync="True")        # TODO: extend selection List based on FS Values
    lang = fields.Selection(sosync="True")          # ATTENTION: All langs that are used by Fundrasing Studio must be installed manually in FS-Online!
    BPKRequestIDS = fields.One2many(sosync="True")

    # Standard basic fields
    is_company = fields.Boolean(sosync="True")
    name = fields.Char(sosync="True")
    firstname = fields.Char(sosync="True")
    lastname = fields.Char(sosync="True")
    phone = fields.Char(sosync="True")
    mobile = fields.Char(sosync="True")
    fax = fields.Char(sosync="True")
    email = fields.Char(sosync="True")
    opt_out = fields.Char(sosync="True")            # Keine Kommunikation


    # Standard address fields
    street = fields.Char(sosync="True")
    street2 = fields.Char(sosync="True")
    city = fields.Char(sosync="True")
    zip = fields.Char(sosync="True")

    # Website related fields
    website_published = fields.Boolean(sosync="True")


    # Custom FS-Online fields
    anrede_individuell = fields.Char(sosync="True")
    title_web = fields.Char(sosync="True")
    name_zwei = fields.Char(sosync="True")

    birthdate_web = fields.Date(sosync="True")

    company_name_web = fields.Char(sosync="True")

    street_number_web = fields.Char(sosync="True")
    post_office_box_web = fields.Char(sosync="True")

    newsletter_web = fields.Boolean(sosync="True")                  # Newsletter OptIn
    donation_receipt_web = fields.Boolean(sosync="True")            # Spendenquittung
    donation_deduction_optout_web = fields.Boolean(sosync="True")   # Spenden autom. absetzten
    legal_terms_web = fields.Boolean(sosync="True")                 # Accept legal terms (webshop)

    # BKP Forced Fields
    BPKForcedFirstname = fields.Char(sosync="True")
    BPKForcedLastname = fields.Char(sosync="True")
    BPKForcedBirthdate = fields.Char(sosync="True")
