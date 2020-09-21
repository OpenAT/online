# -*- coding: utf-8 -*-
from openerp import fields, models, api
from openerp.addons.connector.session import ConnectorSession
from .getresponse_frst_personemailgruppe_export import ContactExporter
from .helper_connector import get_environment
from openerp.exceptions import except_orm, Warning

import logging

_logger = logging.getLogger(__name__)

class FRSTPersonemailgruppeGRSync(models.Model):
    _name = 'frst.personemailgruppe'
    _inherit = ['frst.personemailgruppe']

    @api.multi
    def prepare_getresponse_binding(self):

        if not self.zgruppedetail_id.sync_with_getresponse:
            raise except_orm('Error',
                             'frst.zgruppedetail "%s" is not set to be synchronized with GetResponse.'
                             % (self.zgruppedetail_id.gruppe_lang))

        connector_session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        backend_obj = self.env['getresponse.backend']
        backends = backend_obj.search([])
        error_dict = {}

        for backend in backends:
            try:
                connector_env = get_environment(connector_session, 'getresponse.frst.personemailgruppe', backend.id)
                record_exporter = connector_env.get_connector_unit(ContactExporter)
                record_exporter.binder.prepare_bindings(self)
            except Exception as e:
                error_dict['%s, %s' % (backend.id, backend.name)] = e.message

        if error_dict:
            messages = ['Backend {0}: {1}'.format(key, value) for key, value in error_dict.iteritems()]
            raise except_orm('Error', '\n'.join(messages))
