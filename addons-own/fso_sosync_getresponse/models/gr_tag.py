# -*- coding: utf-8 -*-

from openerp import models, fields


class GrTagGetResponseSosync(models.Model):
    _name = 'gr.tag'
    _inherit = ['gr.tag', 'base.sosync']

    name = fields.Char(sosync="True")
    type = fields.Selection(sosync="True")

    # Link to the CDS
    cds_id = fields.Many2one(sosync="True")

    # Link res.partner
    partner_ids = fields.Many2many(sosync="True")

    # Optional Extra Information
    description = fields.Text(sosync="True")
    origin = fields.Text(sosync="True")
