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
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools import SUPERUSER_ID


class ResPartner(models.Model):
    _inherit = 'res.partner'
    # Fields for sosyncer to detect origin of res.partner updates by fstoken
    fstoken_update = fields.Char(string='Update by FS Token')
    fstoken_update_date = fields.Datetime(string='Update by FS Token Date')


class WebsiteApfSettings(models.Model):
    _inherit = 'website'

    # Button Text and Headlines
    apf_title_code = fields.Char(string='Code Header', default=_("Your Code"), translate=True)
    apf_title_code_hide = fields.Boolean(string='Hide Code Header')
    apf_token_label = fields.Char(string='Token Label', default=_("Code"),
                                  translate=True)
    apf_token_placeholder = fields.Char(string='Token Placeholder', default="A4N - 53B - XH7 - 4J4", translate=False)
    apf_title_partner_data = fields.Char(string='Your-Data Header', default=_("Your Data"), translate=True)
    apf_title_partner_data_hide = fields.Boolean(string='Hide Your-Data Header')
    apf_logout_button = fields.Char(string='Logout Button', translate=True)
    apf_submit_button = fields.Char(string='Submit Button', default=_("Submit"), translate=True)
    # Snippet Areas
    apf_top_snippets = fields.Html(string='APF Top Snippets', translate=True)
    apf_yourdata_snippets = fields.Html(string='APF Your Data Snippets', translate=True)
    apf_bottom_snippets = fields.Html(string='APF Top Snippets', translate=True)
    apf_update_success_message = fields.Html(string='Update Success Message', translate=True)
    apf_token_success_message = fields.Html(string='Token Success Message', translate=True)
    apf_token_error_message = fields.Html(string='Token Error Message', translate=True)
    # BPK-Status-Snippet Messages
    apf_status_success = fields.Char(string="BPK-Status-Snippet Success", translate=True,
                                     default=_("Great! Donation deduction is possible with your data!"))
    apf_status_error = fields.Char(string="BPK-Status-Snippet Error", translate=True,
                                   default=_("Donation deduction is not possible with this data! "
                                             "Please check your input. "
                                             "The important fields are firstname, lastname and your birthdate."
                                             "Please contact us if you any questions or problems!"))


class ResConfigApfSetting(models.Model):
    _inherit = 'website.config.settings'
    # HINT: in addon website in res_config.py
    # 'website_id': fields.many2one('website', string="website", required=True),
    # defaults={'website_id': lambda self,cr,uid,c: self.pool.get('website').search(cr, uid, [], context=c)[0],}
    apf_title_code = fields.Char(related='website_id.apf_title_code')
    apf_title_code_hide = fields.Boolean(related='website_id.apf_title_code_hide')
    apf_token_label = fields.Char(related='website_id.apf_token_label')
    apf_token_placeholder = fields.Char(related='website_id.apf_token_placeholder')
    apf_title_partner_data = fields.Char(related='website_id.apf_title_partner_data')
    apf_title_partner_data_hide = fields.Boolean(related='website_id.apf_title_partner_data_hide')
    apf_submit_button = fields.Char(related='website_id.apf_submit_button')
    apf_logout_button = fields.Char(related='website_id.apf_logout_button')
    apf_update_success_message = fields.Html(related='website_id.apf_update_success_message')
    apf_token_success_message = fields.Html(related='website_id.apf_token_success_message')
    apf_token_error_message = fields.Html(related='website_id.apf_token_error_message')



class ApfPartnerFields(models.Model):
    """res.partner fields for the website form /meine-daten"""
    _name = 'website.apf_partner_fields'
    _description = '/meine-daten Partner Fields'
    _order = 'sequence, res_partner_field_id'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)
    res_partner_field_id = fields.Many2one('ir.model.fields',
                                           string="res.partner Field",
                                           domain="[('model_id.model', '=', 'res.partner')]")
    mandatory = fields.Boolean(string='Mandatory')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True)
    validation_rule = fields.Char(string='Validation Rule')
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    nodata = fields.Boolean(string='NoData', help='Do not show res.partner data in the website form.')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
    information = fields.Html(string='Information', help='Information Text', translate=True)

    _defaults = {
        'active': True,
    }

    # Remove noupdate for view auth_partner_form.meinedaten on addon update
    def init(self, cr, context=None):
        ir_model_data_obj = self.pool.get('ir.model.data')
        meinedaten_view_id = ir_model_data_obj.search(cr, SUPERUSER_ID,
                                                      ['&',
                                                       ('module', '=', 'auth_partner_form'),
                                                       ('name', '=', 'meinedaten')
                                                       ])
        if meinedaten_view_id and len(meinedaten_view_id) == 1:
            meinedaten_view = ir_model_data_obj.browse(cr, SUPERUSER_ID, meinedaten_view_id)
            meinedaten_view.write({"noupdate": False})

    @api.onchange('show', 'mandatory')
    def oc_show(self):
        if not self.show:
            self.mandatory = False

    @api.onchange('style', 'mandatory')
    def oc_style(self):
        if self.style == 'radio_selectnone':
            self.mandatory = False
