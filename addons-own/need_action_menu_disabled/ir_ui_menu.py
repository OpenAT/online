from openerp import models, api
import logging
logger = logging.getLogger(__name__)


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.multi
    def get_needaction_data(self):
        logger.warning('NEED ACTION COUNTER GLOBALLY DISABLED!')
        res = dict.fromkeys(self.ids, {
                'needaction_enabled': False,
                'needaction_counter': False,
            })
        return res
