# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentAcquirerSosync(models.Model):
    _name = "payment.acquirer"
    _inherit = ["payment.acquirer", "base.sosync"]

    # This model is read-only in FRST!

    name = fields.Char(sosync="fson-to-frst")

    # TO: res.company
    company_id = fields.Many2one(sosync="fson-to-frst")

    # Do not send E-Mails to the donor on payment status changes
    do_not_send_status_email = fields.Boolean(sosync="fson-to-frst")

    # Environment e.g.: Test or Productive
    environment = fields.Selection(sosync="fson-to-frst")

    # Normally hidden in the webpage (can only be activated if explicitly set on OPC products)
    globally_hidden = fields.Boolean(sosync="fson-to-frst")

    # Payment Method Type e.g. VISA (BRAND)
    ogonedadi_brand = fields.Char(sosync="fson-to-frst")

    # Payment Method e.g. Credit Card (PM)
    ogonedadi_pm = fields.Char(sosync="fson-to-frst")

    # Ogone API User ID
    ogonedadi_userid = fields.Char(sosync="fson-to-frst")

    # TO: product.acquirer_lines
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #product_acquirer_lines_ids = fields.One2many(sosync="fson-to-frst")

    provider = fields.Selection(sosync="fson-to-frst")

    # Can be used for recurring transactions
    recurring_transactions = fields.Boolean(sosync="fson-to-frst")

    # Where to return to after payment at the payment provider webpage
    redirect_url_after_form_feedback = fields.Char(sosync="fson-to-frst")

    validation = fields.Selection(sosync="fson-to-frst")

    # Available on the webpage
    website_published = fields.Boolean(sosync="fson-to-frst")
