# -*- coding: utf-'8' "-*-"

from openerp import api, models, fields
import copy

import logging
logger = logging.getLogger(__name__)


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    mass_mailing_ids = fields.One2many(string="Mass Mailing",
                                       comodel_name="mail.mass_mailing", inverse_name="email_template_id",
                                       readonly=True)

    # Compute email_body html to be used in odoo or mass mailing
    fso_email_html_odoo = fields.Text(string='E-Mail HTML odoo',
                                      readonly=True, translate=True,
                                      help="E-Mail HTML code ready to send with a mass mailing!\n"
                                           "URL protocol fixed, Relative URLs converted to static URLs, "
                                           "regular URLs tracked by link_tracker, CSS inlined "
                                           "FRST print fields replaced by mako expressions where possible")

    @api.multi
    def _update_fso_email_html_odoo(self):
        # ---------------------------
        # Compute fso_email_html_odoo
        # ---------------------------
        for r in self:
            if r.fso_email_html:
                content = r.fso_email_html

                # TEST:
                #content = r.body_html

                #assert content is not r.fso_email_html, "Use copy() instead of ="

                # Convert all Fundraising Studio print fields to mako expressions or ''
                fso_print_fields = self.env['fso.print_field'].sudo().search([('fs_email_placeholder', '!=', False)])
                for pf in fso_print_fields:
                    content = content.replace(pf.fs_email_placeholder, pf.mako_expression or '')

                # Set 'fso_email_html_odoo'
                logger.info('Update email.template field fso_email_html_odoo!')
                logger.info('content: %s' % content)
                r.write({'fso_email_html_odoo': content})
            else:
                r.write({'fso_email_html_odoo': False})

        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):

        res = super(EmailTemplate, self).create(values)

        # Update fso_email_html_odoo
        if res and 'fso_email_html' in values:
            res._update_fso_email_html_odoo()

        # Replace 'body_html' used by the send mail with content of 'fso_email_html_odoo' for mass mailing e-mails
        if res and res.mass_mailing_ids:
            if res.fso_email_html_odoo:
                res.mass_mailing_ids.write({'body_html': res.fso_email_html_odoo})
            else:
                logger.error('Field "fso_email_html_odoo" is empty for email template with id %s' % res.id)

        return res

    @api.multi
    def write(self, values):

        res = super(EmailTemplate, self).write(values)

        # Update fso_email_html_odoo
        if res and 'fso_email_html' in values:
            self._update_fso_email_html_odoo()

        if res:
            for r in self:
                if r and r.mass_mailing_ids:
                    if r.fso_email_html_odoo:
                        r.mass_mailing_ids.write({'body_html': r.fso_email_html_odoo})
                    else:
                        logger.error('Field "fso_email_html_odoo" is empty for email template with id %s' % r.id)

        return res
