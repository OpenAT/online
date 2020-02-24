# -*- coding: utf-8 -*-
# © 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# © 2015 Antonio Espinosa <antonioea@antiun.com>
# © 2015 Javier Iniesta <javieria@antiun.com>
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    with api.Environment.manage():
        _logger.info('Compute xml_id field for product.payment_interval')

        env = api.Environment(cr, SUPERUSER_ID, {})
        interval_model = env['product.payment_interval']
        interval_model.compute_all_xml_id()
