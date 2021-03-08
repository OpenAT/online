# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Post(models.Model):
    _inherit = 'forum.post'

    content = fields.Html(strip_style=False)
