# -*- coding: utf-8 -*-
from openerp import models, fields


class BlogBlogSnippets(models.Model):
    _inherit = 'blog.blog'

    snippets_top = fields.Html('Blog Top', translate=True)
    snippets_bottom = fields.Html('Blog Bottom', translate=True)
