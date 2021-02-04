# -*- coding: utf-8 -*-
from openerp import api, fields, models

import logging
logger = logging.getLogger(__name__)


class Namespace(models.Model):

    _inherit = "openapi.namespace"

    @api.model
    def _clean_frst_api_data_before_update(self):
        logger.info("Clear 'frst' rest api data before addon update!")

        ir_exports = self.env['ir.model.data'].search([('module', '=', 'fso_rest_api'),
                                                       ('model', '=', 'ir.exports')])
        to_delete = ir_exports.mapped('complete_name')

        for xml_ref in to_delete:
            logger.info("DELETE: '%s' on install update of fso_rest_api" % xml_ref)
            record = self.sudo().env.ref(xml_ref, raise_if_not_found=False)
            if record:
                record.unlink()
