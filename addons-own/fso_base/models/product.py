# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fs_product_type = fields.Selection(selection=[('product', 'Product'),               # Produkt
                                                  ('donation', 'Donation'),             # Spende
                                                  ('godparenthood', 'Godparenthood'),   # Patenschaft
                                                  ('sponsorship', 'Donation'),          # Foerderer(schaft)
                                                  ('membership', 'Donation'),           # Mitgliedschaft
                                                  ],
                                       string="Fundraising Studio Type")

