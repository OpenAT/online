# -*- coding: utf-'8' "-*-"

from openerp import api, models, fields


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    mass_mailing_ids = fields.One2many(string="Mass Mailing",
                                       comodel_name="mail.mass_mailing", inverse_name="email_template_id",
                                       readonly=True)

    # Compute email_body html to be used in odoo or mass mailing
    fso_email_html_odoo = fields.Text(string='E-Mail HTML odoo', compute='_compute_html', store=True,
                                      readonly=True, translate=True,
                                      help="E-Mail HTML code ready to send with a mass mailing!\n"
                                           "URL protocol fixed, Relative URLs converted to static URLs, "
                                           "regular URLs tracked by link_tracker, CSS inlined "
                                           "FRST print fields replaced by mako expressions where possible")

    def _compute_html(self):
        # Do the regular computation first to update fields fso_email_html, fso_email_html_parsed and screenshot
        super(EmailTemplate, self)._compute_html()

        # ---------------------------
        # Compute fso_email_html_odoo
        # ---------------------------
        for r in self:
            if r.fso_email_html:
                content = r.fso_email_html

                # Convert Fundraising Studio print fields to mako expressions
                # Get all print fields
                print_fields = self.env['fso.print_field'].sudo().search([('fs_email_placeholder', '!=', False),
                                                                          ('mako_expression', '!=', False)])
                for pf in print_fields:
                    content.replace(pf.fs_email_placeholder, pf.mako_expression)

                # Update computed field fso_email_html_odoo
                r.fso_email_html_odoo = content

        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):

        res = super(EmailTemplate, self).create(values)

        if res and res.mass_mailing_ids:
            res.mass_mailing_ids.write({'body_html': res.fso_email_html_odoo})

        # Update body html by email_template_id.fso_email_html_odoo
        return res

    @api.multi
    def write(self, values):

        res = super(EmailTemplate, self).write(values)

        if res:
            for r in self:
                if r and r.mass_mailing_ids:
                    r.mass_mailing_ids.write({'body_html': r.fso_email_html_odoo})

        return res
