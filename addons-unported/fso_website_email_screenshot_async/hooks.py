# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import SUPERUSER_ID


def _set_screenshot_cron_state(cr, registry, active_state):
    cron = registry['ir.model.data'].xmlid_to_object(
        cr, SUPERUSER_ID, 'fso_website_email.ir_cron_scheduled_email_template_screenshot')
    if cron:
        cron.write({'active': active_state})


# Deactivate cron job on install/update
def post_init_hook(cr, registry):
    _set_screenshot_cron_state(cr, registry, active_state=False)


# Reactivate cronjob if addon es uninstalled
def uninstall_hook(cr, registry):
    _set_screenshot_cron_state(cr, registry, active_state=True)
