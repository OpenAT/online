# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTPersonEmailSosync(models.Model):
    _name = "frst.personemail"
    _inherit = ["frst.personemail", "base.sosync"]

    # Use a high priority for emails so that they may be processed before e.g.: 'sale.order.line' or 'gl2k.garden'
    _sync_job_priority = 4500

    email = fields.Char(sosync="True")
    gueltig_von = fields.Date(sosync="True")
    gueltig_bis = fields.Date(sosync="True")
    main_address = fields.Boolean(sosync="True")

    state = fields.Selection(sosync="fson-to-frst")
