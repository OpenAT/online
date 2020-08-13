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

    name = fields.Char(string="Name", required=True)

    # Link res.partner
    partner_ids = fields.Many2many(comodel_name='res.partner', inverse_name='getresponse_tag_ids',
                                   string='Partner with this Tag')

    # Optional Extra Information
    description = fields.Text(string="Description")
    origin = fields.Text(string="Origin", readonly=True, help="Field for FRST to store origin informations.")

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'A tag with this name exists already!'),
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
