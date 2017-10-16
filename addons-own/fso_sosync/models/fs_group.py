# -*- coding: utf-'8' "-*-"
from openerp import models


class FSGroupSosync(models.Model):
    _name = "fs.group"
    _inherit = ["fs.group", "base.sosync"]
