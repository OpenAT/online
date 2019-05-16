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
        _logger.warning('UPDATE SYSTEM USER NAMES')

        def set_name(partners={}, force=False):
            model_data_obj = self.pool.get('ir.model.data')
            partner_obj = self.pool.get('res.partner')
            for xml_ref, vals in partners.iteritems():
                _logger.info('Find partner %s' % xml_ref)
                partner = model_data_obj.xmlid_to_object(cr, SUPERUSER_ID, xml_ref)
                if partner and (force or not partner.lastname):
                    _logger.warning('Update partner %s with vals %s' % (xml_ref, str(vals)))
                    partner_obj.write(cr, SUPERUSER_ID, [partner.id], vals)
                elif not partner:
                    _logger.warning('Partner %s not found' % xml_ref)
                else:
                    _logger.info('Partner %s found but no update is needed' % xml_ref)

        # Hint do use force=True for admin because the name might be used in E-Mail Templates and therefore altered!
        admin = {'base.partner_root': {'firstname': 'FS-Online',
                                       'lastname': 'Administrator'}}
        set_name(admin)

        public = {'base.public_partner': {'firstname': 'FS-Online',
                                          'lastname': 'Website/Public'}}
        set_name(public, force=True)

        sosync = {'base.partner_sosync': {'firstname': 'FS-Online',
                                          'lastname': 'Syncer Service'}}
        set_name(sosync, force=True)

        sosync_frst = {'base.partner_studio': {'firstname': 'FS-Online',
                                               'lastname': 'Syncer FRST-Access'}}
        set_name(sosync_frst, force=True)

        consale = {'fson_connector_sale.partner_consale_admin': {'firstname': 'FS-Online',
                                                                 'lastname': 'Webschnittstelle'}}
        set_name(consale, force=True)
