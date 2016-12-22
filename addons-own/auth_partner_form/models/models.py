# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    # Fields for sosyncer to detect origin of res.partner updates by fstoken
    fstoken_update = fields.Char(string='Update by FS Token')
    fstoken_update_date = fields.Datetime(string='Update by FS Token Date')


class WebsiteApfSettings(models.Model):
    _inherit = 'website'

    # Button Text and Headlines
    apf_title_code = fields.Char(string='Code Header', default="Your Code", translate=True)
    apf_token_label = fields.Char(string='Token Label', default="Code without dashes", translate=True)
    apf_token_placeholder = fields.Char(string='Token Placeholder', default="A4N - 53B - XH7 - 4J4", translate=False)
    apf_title_partner_data = fields.Char(string='Your-Data Header', default="Your Data", translate=True)
    apf_submit_button = fields.Char(string='Submit Button', default="Submit", translate=True)
    # Snippet Areas
    apf_top_snippets = fields.Html(string='APF Top Snippets', translate=True)
    apf_bottom_snippets = fields.Html(string='APF Top Snippets', translate=True)


class ResConfigApfSetting(models.Model):
    _inherit = 'website.config.settings'
    # HINT: in addon website in res_config.py
    # 'website_id': fields.many2one('website', string="website", required=True),
    # defaults={'website_id': lambda self,cr,uid,c: self.pool.get('website').search(cr, uid, [], context=c)[0],}
    apf_title_code = fields.Char(related='website_id.apf_title_code')
    apf_token_label = fields.Char(related='website_id.apf_token_label')
    apf_token_placeholder = fields.Char(related='website_id.apf_token_placeholder')
    apf_title_partner_data = fields.Char(related='website_id.apf_title_partner_data')
    apf_submit_button = fields.Char(related='website_id.apf_submit_button')


class ApfPartnerFields(models.Model):
    """res.partner fields for the website form /meine-daten"""
    _name = 'website.apf_partner_fields'
    _description = '/meine-daten Partner Fields'
    _order = 'sequence, res_partner_field_id'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)
    res_partner_field_id = fields.Many2one('ir.model.fields',
                                           string="res.partner Field",
                                           domain="[('model_id.model', '=', 'res.partner')]",
                                           required=True)
    mandatory = fields.Boolean(string='Mandatory')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True)
    validation_rule = fields.Char(string='Validation Rule')
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    information = fields.Html(string='Information', help='Information Text', translate=True)

    _defaults = {
        'active': True,
    }
