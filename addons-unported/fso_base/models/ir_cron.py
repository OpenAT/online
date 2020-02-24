# -*- coding: utf-'8' "-*-"
from openerp import api, models
from openerp.addons.fso_base.tools.email_tools import send_internal_email

import logging
logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = 'ir.cron'

    @api.multi
    def write(self, vals):
        res = super(IrCron, self).write(vals)

        try:
            if vals.get('active', 'not_found') is False:
                job_info = tuple((r.name, r.id) for r in self)
                msg = "WARNING: Cron Job(s) %s deactivated" % str(job_info)
                logging.warning(msg)
                send_internal_email(odoo_env_obj=self.env, subject=msg, body=msg)
        except Exception as e:
            logging.error(repr(e))
            pass

        return res
