# -*- coding: utf-'8' "-*-"

from openerp import api, models, fields


class MailComposeMessage(models.Model):
    _inherit = 'mail.compose.message'

    @api.model
    def create(self, vals):

        # ATTENTION: Add link tracker urls and change url schema (like in MassMailing.send_mail() in odoo 11.)
        #            Would be better to change the send_mail() of mail.mass_mailing but this is not possible
        #            since the values created for the composer are not in an extra method - so the only option would be
        #            to completely overwrite the send_mail() method which of course is bad for inheritance. Therefore
        #            we intercept the create() method of mail.compose.message and change the body html there because
        #            this is directly called in send_mail() with the composer values
        #            ['mail.compose.message'].create(cr, uid, composer_values, context=comp_ctx)
        if vals.get('mass_mailing_id'):
            mass_mailing = self.env['mail.mass_mailing'].browse([vals.get('mass_mailing_id')])
            if mass_mailing.email_template_id:
                # ATTENTION: Make sure that the body_html is already the body from the FS-Online email template
                #            This is done in the CRUD methods of mail.mass_mailing and email_template in this addon
                # ATTENTION: URLs must already be absolute at this point!
                created_bodys = mass_mailing.convert_links()
                vals['body'] = created_bodys[mass_mailing.id]

        res = super(MailComposeMessage, self).create(vals)
        return res
