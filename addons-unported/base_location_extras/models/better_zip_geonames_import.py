# -*- coding: utf-8 -*-
# © 2014 Alexis de Lattre <alexis.delattre@akretion.com>
# © 2014 Lorenzo Battistini <lorenzo.battistini@agilebg.com>
# © 2016 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class BetterZipGeonamesImport(models.TransientModel):
    _inherit = "better.zip.geonames.import"

    @api.model
    def _prepare_better_zip(self, row, country):
        vals = super(BetterZipGeonamesImport, self)._prepare_better_zip(row, country)
        vals.update({
            'county_province': row[5],
            'county_province_code': row[6],
            'community': row[7],
            'community_code': row[8],
            'latitude': row[9],
            'longitude': row[10],
            'accuracy': row[11],
        })
        return vals
