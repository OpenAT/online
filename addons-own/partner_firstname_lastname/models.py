# -*- coding: utf-8 -*-

#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Copyright (C)
#       2014:       Agile Business Group (<http://www.agilebg.com>)
#       2015:       Grupo ESOC <www.grupoesoc.es>
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

from openerp import api, fields, models
from openerp import SUPERUSER_ID
import logging


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_computed_name(self, lastname, firstname):
        # Fully Overwrite the original method to inverse the name
        return u" ".join((p for p in (firstname, lastname) if p))

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        name_parts = super(ResPartner, self)._get_inverse_name(name=name, is_company=is_company)
        # Invert the original Result:
        return {"lastname": name_parts['firstname'], "firstname": name_parts['lastname']}

    def init(self, cr, context=None):
        # Update all res.partner.name fields on addon install or update if there is already a lastname
        partners = self.search(cr, SUPERUSER_ID, [])
        partner_updates = 0
        for partner_id in partners:
            partner = self.browse(cr, SUPERUSER_ID, [partner_id])
            if partner:
                if partner._get_computed_name(partner.lastname, partner.firstname) != partner.name:
                    partner.write({"lastname": partner.lastname})
                    partner_updates += 1
        _logger.info('Recalculation of res.partner.name field was needed for %s partner(s)' % partner_updates)

