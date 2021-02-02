# -*- coding: utf-8 -*-
from openerp import api, fields, models

import logging
logger = logging.getLogger(__name__)


class Namespace(models.Model):

    _inherit = "openapi.namespace"

    @api.model
    def _clean_frst_api_data_before_update(self):
        logger.info("Clear 'frst' rest api data before addon update!")

        to_delete = ('fso_rest_api.frst_rest_api_res_partner_export',)

        for xml_ref in to_delete:
            record = self.sudo().env.ref(xml_ref, raise_if_not_found=False)
            if record:
                record.unlink()
