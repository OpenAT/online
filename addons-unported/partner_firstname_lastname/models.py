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
import logging
import time


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

    # Overwrite method to make it possible to update the name field without updating firstname and lastname
    @api.one
    def _inverse_name_after_cleaning_whitespace(self):
        # Skip the inverse function (= do not update firstname lastname) and reset it for the next regular change
        if self.env.context.get("partner_firstname_skip_inverse"):
            # Do not skip next change
            self.env.context = self.with_context(partner_firstname_skip_inverse=False).env.context
        else:
            super(ResPartner, self)._inverse_name_after_cleaning_whitespace()

    # DEPRACTED use def _install_update_...
    # def init(self, cr, context=None):
    #     # Check all res.partner.name field on addon install or update
    #     partners = self.search(cr, SUPERUSER_ID, [])
    #     partner_updates = 0
    #     for partner_id in partners:
    #         partner = self.browse(cr, SUPERUSER_ID, [partner_id])
    #         if partner:
    #             computed_name = partner._get_computed_name(partner.lastname, partner.firstname)
    #             if computed_name != partner.name:
    #                 # Avoid recursive update of firstname and lastname fields if field name changes
    #                 if context:
    #                     context['partner_firstname_skip_inverse'] = True
    #                 else:
    #                     context = {'partner_firstname_skip_inverse': True}
    #                 partner.write(cr, SUPERUSER_ID, {"name": computed_name}, context=context)
    #                 partner_updates += 1
    #     _logger.info('Recalculation of res.partner.name field was needed for %s partner(s)' % partner_updates)

    # DISABLED because of performance problems for very large dbs
    # @api.model
    # def _install_update_partner_firstname_lastname(self):
    #     partner_updates = 0
    #     start_time = time.time()
    #     partners = self.search([])
    #     _logger.info("Checking \"name\" field for %d res.partner on update of the addon.", len(partners))
    #     for partner in partners:
    #         computed_name = partner._get_computed_name(partner.lastname, partner.firstname)
    #         if computed_name != partner.name:
    #             # Avoid inverse function of the "name" field (= do not change firstname or lastname)
    #             self.env.context = self.with_context(partner_firstname_skip_inverse=True).env.context
    #             partner.name = computed_name
    #             partner_updates += 1
    #     # Log Result
    #     total_time = time.time()-start_time
    #     _logger.info('Update of %s partner(s) in %.0f sec (%.1f min)' % (partner_updates, total_time, total_time/60))

