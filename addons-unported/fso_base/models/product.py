# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fs_product_type = fields.Selection(selection=[('donation', 'Donation'),              # Spende: includes Patenschaft, Foerderer(schaft),
                                                  #('godparenthood', 'Godparenthood'),   # Patenschaft
                                                  #('sponsorship', 'Sponsorship'),       # Foerderer(schaft)
                                                  #('membership', 'Membership'),         # Mitgliedschaft
                                                  ('product', 'Product'),                # Produkt: includes Mitgliedschaft, Event Ticket
                                                  #('eventticket', 'Event Ticket'),      # Event Ticket
                                                  ('mediation', 'Mediation'),            # e.g. Tiervermittlung
                                                  ],
                                       string="Type")
