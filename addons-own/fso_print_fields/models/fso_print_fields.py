# -*- coding: utf-8 -*-
from openerp import models, fields, api


class FsoPrintField(models.Model):
    _name = 'fso.print_field'
    _order = 'sequence ASC'

    # ------
    # FIELDS
    # ------
    name = fields.Char(string="Anzeige Name", translate=True, required=True)
    sequence = fields.Integer(string="Seq.", default=1000)

    # Fundraising Studio Placeholder
    fs_email_placeholder = fields.Char(string="Fundraising Studio E-Mail Placeholder", required=True,
                                       help="e.g.: %Name%", readonly=True)

    mako_expression = fields.Char(string="Odoo Mako Expression",
                                  help="e.g.: ${object.name}", readonly=True)

    css_class = fields.Char(string="CSS Class", readonly=True, compute="_compute_css_class", store=True)

    # Available in Print Field Snippet(s)
    group_ids = fields.Many2many(string="In Groups", comodel_name="fso.print_field.group")

    # Excluded in E-Mail Theme(s)
    exclude_in_email_theme_ids = fields.Many2many(string="Excluded in E-Mail Themes", comodel_name="ir.ui.view",
                                                  domain="[('fso_email_template','=',True)]")

    @api.depends('fs_email_placeholder')
    def _compute_css_class(self):
        for r in self:
            r.css_class = 'pf_'+r.fs_email_placeholder.replace('%', '').lower() if r.fs_email_placeholder else False


class FsoPrintFieldsGroup(models.Model):
    _name = "fso.print_field.group"

    # ------
    # FIELDS
    # ------
    name = fields.Char(string="Name", translate=True, required=True)
    sequence = fields.Integer(string="Seq.", default=1000)

    # Print Fields in this group (=Snippet)
    print_field_ids = fields.Many2many(string="Print Fields", comodel_name="fso.print_field")

    # Excluded in E-Mail Theme(s)
    exclude_in_email_theme_ids = fields.Many2many(string="Exclude in E-Mail Themes", comodel_name="ir.ui.view",
                                                  domain="[('fso_email_template','=',True)]")


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    # ------
    # FIELDS
    # ------
    excluded_fso_print_field_ids = fields.Many2many(string="Exclude Print Fields",
                                                    comodel_name="fso.print_field")

    excluded_fso_print_field_group_ids = fields.Many2many(string="Exclude Print Field Groups",
                                                          comodel_name="fso.print_field.group")
