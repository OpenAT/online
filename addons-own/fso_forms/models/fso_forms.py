# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.tools import SUPERUSER_ID

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _name = "fson.form"

    _order = 'sequence'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    name = fields.Char(string="Form Name", required=True)

    model_id = fields.Many2one(string="Model", comodel_name="ir.model", required=True)
    model_record_id = fields.Integer(string="Record ID", help="ID of the related model", readonly=True)
    user_id = fields.Integer(string="User ID", help="", readonly=True)

    field_ids = fields.One2many(string="Fields", comodel_name="fson.form_field", inverse_name="form_id")

    submission_url = fields.Char(string="Submission URL", default="/fson/form/submit", required=True)
    redirect_url = fields.Char(string="Redirect URL", default="/fson/form/thanks", required=True,
                               help="Redirect URL after form feedback")

    snippet_area_top = fields.Html(string="Top Snippet Area")
    snippet_area_bottom = fields.Html(string="Bottom Snippet Area")

    @api.constrains('model_id')
    def oc_model_id(self):
        for r in self:
            if any(f.field_id.model_id != r.model_id for f in r.field_ids):
                raise ValidationError("Mismatch between fields and model! Please remove fields first!")


class FSONFormField(models.Model):
    _name = "fson.form_field"
    _order = 'sequence'

    def default_model_id_from_context(self):
        logger.info("GET DEFAULT CONTEXT: %s" % self.env.context)
        return self.env.context.get('model_id', False)

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)

    form_id = fields.Many2one(comodel_name="fson.form", string="Form", required=True,
                              index=True, ondelete='cascade')

    field_id = fields.Many2one(string="Field", comodel_name='ir.model.fields',
                               index=True, ondelete='cascade')

    mandatory = fields.Boolean(string='Mandatory')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True)
    validation_rule = fields.Char(string='Validation Rule')
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    nodata = fields.Boolean(string='NoData', help='Do not show record data in the website form if logged in.')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
    information = fields.Html(string='Information', help='Information Text', translate=True)

    @api.onchange('show', 'mandatory')
    def oc_show(self):
        if not self.show:
            self.mandatory = False

    @api.onchange('style', 'mandatory')
    def oc_style(self):
        if self.style == 'radio_selectnone':
            self.mandatory = False

    @api.onchange('form_id')
    def oc_form_id(self):
        logger.info("YEEEEESSSSS")
        if self.form_id:
            return {'domain': {
                'form_id': [('model_id', '=', self.form_id.model_id)]
            }}
