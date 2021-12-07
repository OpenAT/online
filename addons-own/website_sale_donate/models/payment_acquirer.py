# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api


# new api port
class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence', default=1000)
    recurring_transactions = fields.Boolean(string='Recurring Transactions', default=False)
    acquirer_icon = fields.Binary(string="Acquirer Icon", help="Acquirer Icon 120x90 PNG 32Bit")
    submit_button_text = fields.Char(string='Submit Button Text', help='Only works in FS-Online Payment Methods',
                                     translate=True)
    submit_button_class = fields.Char(string='Submit Button CSS classes',
                                      help='Only works in FS-Online Payment Methods')
    redirect_url_after_form_feedback = fields.Char(string='Redirect URL after PP Form-Feedback',
                                                   help='Redirect to this URL after processing the Answer of the '
                                                        'Payment Provider instead of /shop/confirmation_static',
                                                   translate=True)
    do_not_send_status_email = fields.Boolean(string='Do not send Confirmation E-Mails on TX-State changes.',
                                              help='Will not send website_sale_donate.email_template_webshop. '
                                                   'Setting used in payment provider controllers!')

    post_msg = fields.Html(translate=True)
