# -*- coding: utf-8 -*-
#
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Contributor: Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#                 Ignacio Ibeas <ignacio@acysos.com>
#                 Alejandro Santana <alejandrosantana@anubia.es>
#                 Michael Karrer <michael.karrer@datadialog.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from openerp import models, fields, api


class BetterZip(models.Model):
    _inherit = 'res.better.zip'

    county_province = fields.Char("County/Province")
    county_province_code = fields.Char("County/Province Code")

    community = fields.Char("Community")
    community_code = fields.Char("Community Code")

    latitude = fields.Char("Latitude", help="estimated latitude (wgs84)")
    longitude = fields.Char("Longitude", help="estimated longitude (wgs84)")
    accuracy = fields.Char("Accuracy of Lat/Lng", help="accuracy of lat/lng from 1=estimated to 6=centroid")

    # Create index for delete performance
    state_id = fields.Many2one(index=True)
    country_id = fields.Many2one(index=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Create index for delete performance
    zip_id = fields.Many2one(index=True, ondelete="set null")


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Create index for delete performance
    better_zip_id = fields.Many2one(index=True, ondelete="set null")

