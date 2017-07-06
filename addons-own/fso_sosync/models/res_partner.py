# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "base.sosync"]
    # TODO: dbo.Person relation model: FS has a different model to record relations between partners:
    #       develop new addon for FS-O

    # ACTIVE (= Hidden)
    active = fields.Boolean(sosync="True")          # Record is hidden (will not show up by default in any search)

    # RELATED FIELDS
    parent_id = fields.Many2one(sosync="True")
    state_id = fields.Many2one(sosync="True")
    country_id = fields.Many2one(sosync="True")
    gender = fields.Selection(sosync="True")        # TODO: Extend selection list based on FS-Values
    # ATTENTION: All languages that are used by FS must be installed manually in FS-O!
    lang = fields.Selection(sosync="True")
    BPKRequestIDS = fields.One2many(sosync="True")

    # -----------------------------------------------------------------------------------------------------------------

    # Standard fields
    is_company = fields.Boolean(sosync="True")
    name = fields.Char(sosync="True")
    firstname = fields.Char(sosync="True")
    lastname = fields.Char(sosync="True")
    phone = fields.Char(sosync="True")
    mobile = fields.Char(sosync="True")
    fax = fields.Char(sosync="True")
    email = fields.Char(sosync="True")
    opt_out = fields.Boolean(sosync="True")            # No communication wanted by the partner

    # Standard address fields
    street = fields.Char(sosync="True")
    street2 = fields.Char(sosync="True")
    city = fields.Char(sosync="True")
    zip = fields.Char(sosync="True")

    # Website related fields
    website_published = fields.Boolean(sosync="True")

    # -----------------------------------------------------------------------------------------------------------------

    # FS-Online fields (e.g.: from fso_base)
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
    BPKForcedBirthdate = fields.Date(sosync="True")
