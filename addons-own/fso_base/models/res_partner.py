# -*- coding: utf-'8' "-*-"
from openerp import models, fields, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


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
                                                   help="Donation Deduction OptOut set by Donor",
                                                   track_visibility='onchange', index=True,)
    donation_deduction_disabled = fields.Boolean(string='Donation Deduction Disabled',
                                                 help="Donation Deduction processing disabled by System",
                                                 track_visibility='onchange', index=True,)

    legal_terms_web = fields.Boolean(string='Accept Legal Terms Web')
    birthdate_web = fields.Date(string='Birthdate Web', index=True,)
    anrede_individuell = fields.Char(string='Individuelle Anrede',
                                     help="Eine individuelle Anrede die für den Schriftverkehr verwendet wird.")
    name_zwei = fields.Char(string='Name Zwei',
                            help="Name zweite Zeile für Fundraising Studio")

    # Just enable the index
    firstname = fields.Char(index=True)
    lastname = fields.Char(index=True)

    # DISABLED FOR NOW: Extend the gender field for all FS options
    # ATTENTION: Makes for web no sense therefore disabled!
    #gender = fields.Selection(selection_add=[('male_male', 'Male/Male'),
    #                                         ('female_female', 'Female/Female'),
    #                                         ('female_male', 'Female/Male'),
    #                                         ('male_female', 'Male/Female'),
    #                                         ])

    def init(self, cr, context=None):
        _logger.info('def init: Set firstname and lastname for public user and partner for FRST sync')
        model_data_obj = self.pool.get('ir.model.data')
        public_partner = model_data_obj.xmlid_to_object(cr, SUPERUSER_ID, 'base.public_partner')
        partner_obj = self.pool.get('res.partner')
        if public_partner and not public_partner.lastname:
            _logger.info('def init: Public Partner found and lastname is not set! UPDATING name for FRST sync!')
            partner_obj.write(cr, SUPERUSER_ID, [public_partner.id],
                              {'firstname': 'FS-Online Public/Website',
                               'lastname': 'System-User (do not delete or edit)'})
        elif not public_partner:
            _logger.error('PUBLIC PARTNER NOT FOUND ?!?')

        _logger.info('def init: Set firstname and lastname for admin user and partner for FRST sync')
        admin_partner = model_data_obj.xmlid_to_object(cr, SUPERUSER_ID, 'base.partner_root')
        if admin_partner and (not admin_partner.firstname or not admin_partner.lastname):
            _logger.info('def init: Admin Partner found and lastname is not set! UPDATING name for FRST sync!')
            partner_obj.write(cr, SUPERUSER_ID, [admin_partner.id],
                              {'firstname': 'FS-Online Administrator',
                               'lastname': 'System-User (do not delete or edit)'})
        elif not admin_partner:
            _logger.error('ADMIN PARTNER NOT FOUND ?!?')
