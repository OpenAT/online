# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTzGruppeDetailSosync(models.Model):
    _inherit = "frst.zgruppedetail"

    sync_with_getresponse = fields.Boolean(sosync="True")
