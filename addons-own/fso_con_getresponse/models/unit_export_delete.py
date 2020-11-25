# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier, Michael Karrer
#    Copyright 2013 Camptocamp SA
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
##############################################################################
"""
Delete data from GetResponse.
"""
import logging

from openerp.tools.translate import _

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter

from .helper_connector import get_environment


_logger = logging.getLogger(__name__)


# HINT: Only use the @getresponse decorator on the class where you define _model_name but not on the parent classes!
class GetResponseDeleteExporter(Deleter):
    """ Common flow to export deletes to GetResponse """

    def run(self, getresponse_id):
        """

        Args:
            getresponse_id:

        Returns:
            bool: True if the deletion was successful in GetResponse, False if it failed
        """
        result = self.backend_adapter.delete(getresponse_id)
        if not result:
            raise Exception("Could not delete record %s in GetResponse!" % getresponse_id)

        # Deactivate the binding after we deleted the record in GetResponse
        binding = self.binder.to_openerp(getresponse_id)
        if binding and binding.active:
            _logger.warning("The binding '%s', '%s', odoo_id: '%s', getresponse_id: '%s' was deactivated "
                            "after deleting the record in GetResponse!"
                            "" % (binding._name, binding.id, binding.odoo_id, binding.getresponse_id))
            binding.write({'active': False})
        else:
            _logger.error("No binding found to deactivate for getresponse_id '%s'" % getresponse_id)

        return _('Record %s deleted in GetResponse') % getresponse_id


@job(default_channel='root.getresponse')
def export_delete_record(session, model_name, backend_id, getresponse_id):
    """ Delete a record in GetResponse """

    # Get an connector environment
    connector_env = get_environment(session, model_name, backend_id)

    # ATTENTION: The GetResponseDeleter class may be changed by the model specific implementation!
    #            The connector knows which classes to consider based on the _model_name of the class and the
    #            'model_name' in the args of import_record used in the connector environment above
    deleter = connector_env.get_connector_unit(GetResponseDeleteExporter)
    _logger.info("DELETE RECORD %s IN GETRESPONSE!" % getresponse_id)
    # Start the .run() method of the found exporter class
    return deleter.run(getresponse_id)
