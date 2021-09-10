# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


class XMLIDField(models.AbstractModel):
    _name = 'xml_id.field'

    xml_id = fields.Char(string="XML_ID",
                         readonly=True,
                         compute="compute_xml_id",
                         store=True)

    @api.multi
    def compute_xml_id(self):
        for r in self:
            ext_ids = r.get_external_id()
            r.xml_id = ext_ids.get(r.id, False)

    @api.model
    def compute_all_xml_id(self):
        missing = self.search([('xml_id', '=', False)])
        _logger.info("Compute field xml_id for %s records for model %s" % (len(missing), self._name))
        missing.compute_xml_id()

    def init(self, cr, context=None):
        if self._name != 'xml_id.field':
            self.compute_all_xml_id(cr, SUPERUSER_ID, context=context)

        # super(XMLIDField, self).init(cr, context=context)
