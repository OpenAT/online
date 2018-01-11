# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentAcquirerSosync(models.Model):
    _name = "payment.acquirer"
    _inherit = ["payment.acquirer", "base.sosync"]

    name = fields.Char(sosync="True")

    # TO: res.company
    company_id = fields.Many2one(sosync="True")

    # Do not send E-Mails to the donor on payment status changes
    do_not_send_status_email = fields.Boolean(sosync="True")

    # Environment e.g.: Test or Productive
    environment = fields.Selection(sosync="True")

    # Normally hidden in the webpage (can only be activated if explicitly set on OPC products)
    globally_hidden = fields.Boolean(sosync="True")

    # Payment Method Type e.g. VISA (BRAND)
    ogonedadi_brand = fields.Char(sosync="True")

    # Payment Method e.g. Credit Card (PM)
    ogonedadi_pm = fields.Char(sosync="True")

    # Ogone API User ID
    ogonedadi_userid = fields.Char(sosync="True")

    # TO: product.acquirer_lines
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #product_acquirer_lines_ids = fields.One2many(sosync="True")

    provider = fields.Selection(sosync="True")

    # Can be used for recurring transactions
    recurring_transactions = fields.Boolean(sosync="True")

    # Where to return to after payment at the payment provider webpage
    redirect_url_after_form_feedback = fields.Char(sosync="True")

    validation = fields.Selection(sosync="True")

    # Available on the webpage
    website_published = fields.Boolean(sosync="True")
