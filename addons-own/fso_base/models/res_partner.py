# -*- coding: utf-'8' "-*-"
from openerp import models, fields


# Additional fields for the web checkout
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # New res.partner fields for Fundraising Studio
    # HINT: fore_name_web is DEPRECATED use firstname from partner_firstname_lastname addon
    fore_name_web = fields.Char(string='Fore Name Web DEPRICATED use partner_firstname addon')
    title_web = fields.Char(string='Title Web')
    company_name_web = fields.Char(string='Company Name Web')
    street_number_web = fields.Char(string='Street Number Web')
    post_office_box_web = fields.Char(string='Post Office Box Web')
    newsletter_web = fields.Boolean(string='Newsletter Web')
    donation_receipt_web = fields.Boolean(string='Donation Receipt Web')

    # HINT: SPAK Spendenabsetzbarkeit - Felder zum deaktivieren der automatischen Spendenabsetzung
    #       = keine BPK Anfragen und keine Spendenuebermittlung an das ZMR
    # ATTENTION: These fields are here because they may be useful even without fso_con_zmr
    donation_deduction_optout_web = fields.Boolean(string='Donation Deduction OptOut Web',
                                                   help="Donation Deduction OptOut set by Donor")
    donation_deduction_disabled = fields.Boolean(string='Donation Deduction Disabled',
                                                 help="Donation Deduction processing disabled by System")

    legal_terms_web = fields.Boolean(string='Accept Legal Terms Web')
    birthdate_web = fields.Date(string='Birthdate Web')
    anrede_individuell = fields.Char(string='Individuelle Anrede',
                                     help="Eine individuelle Anrede die für den Schriftverkehr verwendet wird.")
    name_zwei = fields.Char(string='Name Zwei',
                            help="Name zweite Zeile für Fundraising Studio")
