# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields, SUPERUSER_ID
from openerp.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


# Additional fields for the web checkout
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # MISSING INDEXES
    #write_uid = fields.Many2one(index=True)
    #create_uid = fields.Many2one(index=True)

    country_id = fields.Many2one(index=True)
    state_id = fields.Many2one(index=True)

    title = fields.Many2one(index=True)
    user_id = fields.Many2one(index=True)       # TODO: Check the addon of this field!

    assigned_partner_id = fields.Many2one(index=True)
    associate_member = fields.Many2one(index=True)
    grade_id = fields.Many2one(index=True)
    section_id = fields.Many2one(index=True)
    payment_responsible_id = fields.Many2one(index=True)

    # New res.partner fields for Fundraising Studio
    # HINT: fore_name_web is DEPRECATED use firstname from partner_firstname_lastname addon
    fore_name_web = fields.Char(string='Fore Name Web DEPRICATED use partner_firstname addon')
    title_web = fields.Char(string='Title Web')
    company_name_web = fields.Char(string='Company Name Web')
    street_number_web = fields.Char(string='Street Number Web')
    post_office_box_web = fields.Char(string='Post Office Box Web')
    newsletter_web = fields.Boolean(string='Newsletter Web', track_visibility='onchange')
    donation_receipt_web = fields.Boolean(string='Donation Receipt Web')

    # HINT: SPAK Spendenabsetzbarkeit - Felder zum deaktivieren der automatischen Spendenabsetzung
    #       = keine BPK Anfragen und keine Spendenuebermittlung an das ZMR
    # ATTENTION: These fields are here because they may be useful even without fso_con_zmr
    donation_deduction_optout_web = fields.Boolean(string='Donation Deduction OptOut Web',
                                                   help="Donation Deduction OptOut set by Donor",
                                                   track_visibility='onchange')
    donation_deduction_disabled = fields.Boolean(string='Donation Deduction Disabled',
                                                 help="Donation Deduction processing disabled by System",
                                                 track_visibility='onchange')

    legal_terms_web = fields.Boolean(string='Accept Legal Terms Web')
    birthdate_web = fields.Date(string='Birthdate Web', track_visibility='onchange')
    anrede_individuell = fields.Char(string='Individuelle Anrede',
                                     help="Eine individuelle Anrede die für den Schriftverkehr verwendet wird.")
    name_zwei = fields.Char(string='Name Zwei',
                            help="Name zweite Zeile für Fundraising Studio")

    # Just enable the index
    firstname = fields.Char(index=True, track_visibility='onchange')
    lastname = fields.Char(index=True, track_visibility='onchange')

    # DISABLED FOR NOW: Extend the gender field for all FS options
    # ATTENTION: Makes for web no sense therefore disabled!
    #gender = fields.Selection(selection_add=[('male_male', 'Male/Male'),
    #                                         ('female_female', 'Female/Female'),
    #                                         ('female_male', 'Female/Male'),
    #                                         ('male_female', 'Male/Female'),
    #                                         ])

    @api.multi
    def unlink(self):

        # Check if any of the partners has a user attached that belongs to group 'base.group_user'
        if self:
            users = self.env['res.users'].sudo().search([('partner_id', 'in', self.ids)])
            if any(u.has_group('base.group_user') for u in users):
                raise ValidationError('You can not delete a partner linked to a user that belongs to the '
                                      '"base.group_user" group! (partner ids: %s)' % self.ids)

        return super(ResPartner, self).unlink()

    @api.model
    def update_system_user_names_for_firstname_lastname_addon(self):
        _logger.info('UPDATE SYSTEM USER NAMES FOR FIRSTNAME-LASTNAME-ADDON AND TO SUPPORT SOSYNC V2')

        def set_name(partners={}, force=False):
            for xml_ref, vals in partners.iteritems():
                _logger.info('Find partner %s' % xml_ref)

                # Find Partner
                partner = self.sudo().env.ref(xml_ref, raise_if_not_found=False)

                # Update Partner
                if partner and (force or not partner.lastname):
                    _logger.warning('Update partner %s with vals %s' % (xml_ref, str(vals)))
                    try:
                        partner.write(vals)
                    except Exception as e:
                        _logger.error("Could not update partner!\n%s" % repr(e))
                elif not partner:
                    _logger.warning('Partner %s not found' % xml_ref)
                else:
                    _logger.info('Partner %s found but no update is needed' % xml_ref)

        # Hint do !NOT! use force=True for admin because the user might be altered and used in E-Mail Templates!
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
