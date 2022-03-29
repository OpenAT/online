# -*- coding: utf-8 -*-

from openerp import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class ProductPublicCategoryGoal(models.Model):
    _inherit = 'product.public.category'

    goal = fields.Float(string="Funding goal")
    goal_reached = fields.Integer(string="Funding goal reached %",
                                  compute="_cmp_goal_reached",
                                  store=False)

    product_tmpl_ids = fields.Many2many(string='Funding goal products',
                                        comodel_name="product.template",
                                        relation="product_public_category_product_template_rel",
                                        inverse_name="public_categ_ids")

    @api.depends('goal', 'goal_reached', 'product_tmpl_ids.public_categ_ids')  # product_variant_ids
    def _cmp_goal_reached(self):
        for r in self:
            _logger.debug("Updating goal_reached for product.public.category id: %s" % r.id)
            goal_reached = 0

            if r.goal:
                product_income = sum([p.sold_total for p in r.product_tmpl_ids])

                # Calculate reached %, cap at 100%
                goal_reached = min(product_income / r.goal * 100, 100)
            else:
                _logger.debug("No goal set for product.public.category id: %s" % r.id)

            r.goal_reached = goal_reached
