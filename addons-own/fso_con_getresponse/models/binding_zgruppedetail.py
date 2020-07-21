# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import models, fields


# The binding is the link between an Odoo record and an external record. There is no forced implementation for the
# bindings. The most straightforward techniques are: storing the external ID in the same model (account.invoice),
# in a new link model or in a new link model which uses delegation inheritance (_inherits)
# WARNING: When using delegation inheritance, methods are not inherited, only fields!

class GetResponseCampaign(models.Model):
    _name = 'getresponse.frst.zgruppedetail'
    _inherits = {'frst.zgruppedetail': 'odoo_id'}
    _description = 'GetResponse Campaign (List)'

    backend_id = fields.Many2one(comodel_name='getresponse.backend', string='GetResponse Backend',
                                 required=True, ondelete='restrict')

    # HINT: If we delete a FRST group (zGruppeDetail) in odoo or FRST we do not want the GetResponse campaing to be
    #       deleted to. Instead one must first delete the GetResponseCampaign and then delete the FRST group!
    odoo_id = fields.Many2one(comodel_name='frst.zgruppedetail',
                              string='Fundraising Studio Group',
                              required=True, ondelete='restrict')
    getresponse_id = fields.Char(string='GetResponse Campaing ID', readonly=True)
    sync_date = fields.Datetime(string='Last synchronization date', readonly=True)
    sync_data = fields.Char(string='Last synchronization data', readonly=True)

    # Getresponse Campaign Fields
