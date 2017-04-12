# -*- coding: utf-8 -*-
from openerp import api, models, fields


class CompanyAustrianZMRSettings(models.Model):
    _inherit = 'res.company'

    # Basic Settings
    Stammzahl = fields.Char(string="Firmenbuch-/ Vereinsregisternummer", help='Stammzahl e.g.: XZVR-123456789')

    # PVPToken userPrincipal
    pvpToken_userId = fields.Char(string="User ID (userId)")
    pvpToken_cn = fields.Char(string="Common Name (cn)")
    pvpToken_gvOuId = fields.Char(string="Request Organisation (gvOuId)")
    pvpToken_ou = fields.Char(string="Request Person (ou)")

    # SSL Zertifikate
    crt_pem = fields.Binary(string="Certificate (PEM)", help="crt_pem")
    prvkey_pem = fields.Binary(string="Private Key (PEM)", help="prvkey_pem without password!")


class ResPartnerZMRGetBPK(models.Model):
    _inherit = 'res.partner'

    # Get the re
    @api.model
    def GetBPK(self, firstname=str(), lastname=str(), birthdate=str(), decrypted=True):
        bpk = False
        # Validate input
        # Get ZMR Data from default company
        cmp = self.env.user.company
        # Read jinja Templates
        #     https://www.odoo.com/de_DE/forum/hilfe-1/question/is-there-a-way-to-get-the-location-to-your-odoo-and-to-create-new-files-in-your-custom-module-89677
        # Render jinja templates with data
        # Make soap request vis fso_base.tools.soap soap_request()
        # Process soap answer
        return bpk

    @api.multi
    def PartnerGetBPK(self):
        for partner in self:
            # call partner.GetBPK() with correct Settings for Every Record and Update it

