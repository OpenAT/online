# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID

import logging
logger = logging.getLogger(__name__)


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

    # Info / help about the field
    info = fields.Text(string="Information")

    @api.depends('fs_email_placeholder')
    def _compute_css_class(self):
        for r in self:
            r.css_class = 'pf_'+r.fs_email_placeholder.replace('%', '').lower() if r.fs_email_placeholder else False

    def init(self, cr, context=None):
        try:
            logger.warning("Deleting print fields on init or update to make sure we use latest data from xml!")
            pf_obj = self.pool.get('fso.print_field')
            pf_ids = pf_obj.search(cr, SUPERUSER_ID, [])
            pf_obj.unlink(cr, SUPERUSER_ID, pf_ids, context=context)
            # self.env['fso.print_field'].sudo().search([]).unlink()
        except Exception as e:
            logger.error("Could not delete print fields before init/update: %s" % repr(e))


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

    def init(self, cr, context=None):
        try:
            logger.warning("Deleting print field groups on init or update to make sure we use latest data from xml!")
            pfg_obj = self.pool.get('fso.print_field.group')
            pfg_ids = pfg_obj.search(cr, SUPERUSER_ID, [])
            pfg_obj.unlink(cr, SUPERUSER_ID, pfg_ids, context=context)
            # self.env['fso.print_field.group'].sudo().search([]).unlink()
        except Exception as e:
            logger.error("Could not delete print field groups before init/update: %s" % repr(e))


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    # ------
    # FIELDS
    # ------
    excluded_fso_print_field_ids = fields.Many2many(string="Exclude Print Fields",
                                                    comodel_name="fso.print_field")

    excluded_fso_print_field_group_ids = fields.Many2many(string="Exclude Print Field Groups",
                                                          comodel_name="fso.print_field.group")
