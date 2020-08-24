# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# ----------------
# Custom field mappings for GetResponse!
# ----------------
import re

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import ValidationError


# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GrTag(models.Model):
    """ Tag Definitions for GetResponse """
    _name = 'gr.tag'
    _description = 'GetResponse Tag Definition'

    _no_change_after_create = ['name', 'type', 'cds_id']

    name = fields.Char(string="Name", required=True)
    type = fields.Selection(string="Type", selection=[('manual', 'manual'), ('system', 'system')],
                            default='manual', required=True,
                            help="Manual tags are created by the user, system tags are created automatically by"
                                 "Fundraising Studio and should NEVER be created manually!")
    # Link to the CDS
    cds_id = fields.Many2one(string="CDS",
                             comodel_name='frst.zverzeichnis', inverse_name='gr_tag_ids')

    # Link res.partner
    partner_ids = fields.Many2many(comodel_name='res.partner', inverse_name='getresponse_tag_ids',
                                   string='Partner with this Tag')

    # Optional Extra Information
    description = fields.Text(string="Description")
    origin = fields.Text(string="Origin", readonly=True, help="Field for FRST to store origin informations.")

    # ----------
    # CONSTRAINS
    # ----------
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'A tag with this name exists already!'),
        ('cds_id_uniq', 'unique(cds_id)', 'An other tag is set for this CDS entry!'),
    ]

    @api.constrains('name')
    def _constrain_name(self):
        for r in self:
            assert 2 <= len(r.name) <= 255, "The tag name '%s' must be between 2 and 255 characters!" % r.name
            # HINT: The Getresponse API would allow uppercase letters but would convert them to lowercases
            #       anyway. This means tag names are case insensitive. For that reason we only allow lowercase in
            #       in the first place!
            assert re.match(r"(?:[a-z0-9_]+)\Z", r.name, flags=0), _(
                                "Only a-z, 0-9 and _ is allowed for the Tag name: '{}'! ").format(r.name)

    @api.constrains('cds_id')
    def _constrain_cds_id(self):
        for r in self:
            if r.cds_id:
                assert not r.cds_id.verzeichnistyp_id, _("You can not select a CDS folder!")

    @api.multi
    def write(self, values):

        # Constrain changes to some fields after the creation
        if any(f_name in values for f_name in self._no_change_after_create):
            for r in self:
                for f_name in self._no_change_after_create:
                    if f_name in values:
                        assert getattr(r, f_name) == values[f_name], _(
                            "You can not change field %s after tag creation!" % f_name)

        return super(GrTag, self).write(values)

    @api.multi
    def unlink(self):
        if any(r.partner_ids for r in self):
            raise ValidationError("You can not delete Tags that are still assigned to parnter!")

        return super(GrTag, self).unlink()


class GrTagResPartner(models.Model):
    _inherit = 'res.partner'

    # Link GetResponse Tags
    getresponse_tag_ids = fields.Many2many(comodel_name='gr.tag', inverse_name='partner_ids',
                                           string='Getresponse Tags')


class GrTagFRSTzVerzeichnis(models.Model):
    _inherit = 'frst.zverzeichnis'

    # TODO: possible One2One relation workaround (This may not work with the cds_id_uniq constraint above?!?)
    # https://odoo-development.readthedocs.io/en/latest/dev/py/one2one.html
    gr_tag_ids = fields.One2many(string="GetResponse Tags",
                                 comodel_name='gr.tag', inverse_name='cds_id', readonly=True)

