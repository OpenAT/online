# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTPersonEmailSosync(models.Model):
    _name = "frst.personemail"
    _inherit = ["frst.personemail", "base.sosync"]

    email = fields.Char(sosync="True")
