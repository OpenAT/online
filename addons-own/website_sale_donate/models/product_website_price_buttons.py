# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


# new api port
class product_website_price_buttons(models.Model):
    _name = 'product.website_price_buttons'
    _description = 'Product Website Price Buttons'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence', default=1000)
    name = fields.Char(string='Name', translate=True,
                       help="Leave empty if you want to style the button with snippets!")
    snippets = fields.Html(string='Snippet Dropping Area')
    amount = fields.Float(string='Amount', required=True)
    product_id = fields.Many2one(comodel_name='product.template', inverse_name="price_suggested_ids",
                                 string='Product', required=True, ondelete='cascade')
    css_classes = fields.Char(string='CSS classes')
    clearfix = fields.Boolean(string="Linebreak")
    arbitrary_price = fields.Boolean(string="Arbitrary Price")

    # ATTENTION: Will not work here - maybe it would work in product.template
    # @api.onchange('arbitrary_price')
    # def onchange_arbitrary_price(self):
    #     for r in self:
    #         if r.arbitrary_price:
    #             for button in r.product_id.price_suggested_ids:
    #                 if r.id != button.id and button.arbitrary_price:
    #                     button.arbitrary_price = False

    @api.constrains('arbitrary_price')
    def constrain_arbitrary_price(self):
        for r in self:
            if r.product_id.price_suggested_ids:
                arbitrary_price_records = self.product_id.price_suggested_ids.filtered(lambda rec: rec.arbitrary_price)
                assert len(arbitrary_price_records) <= 1, \
                    _("More than one donation button with 'arbitrary_price' enabled!")
