# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

# import the base controller class to inherit from
from openerp.addons.website_forum_doc.controllers.main import WebsiteDoc


class WebsiteDocPrivate(WebsiteDoc):

    @http.route()
    def toc(self, toc=None, **kwargs):
        cr, uid, context, = request.cr, request.uid, request.context

        # Search again to honor user rights and access rules
        if toc:
            toc_obj = request.registry['forum.documentation.toc']
            toc_ids_list = toc_obj.search(cr, uid, [('id', 'in', toc.ids)], context=context)
            toc = toc_obj.browse(cr, uid, toc_ids_list, context=context)

        return super(WebsiteDocPrivate, self).toc(toc=toc, **kwargs)

    @http.route()
    def post(self, toc, post, **kwargs):
        cr, uid, context, = request.cr, request.uid, request.context

        # Search again to honor user rights and access rules
        if toc:
            toc_obj = request.registry['forum.documentation.toc']
            toc_ids_list = toc_obj.search(cr, uid, [('id', 'in', toc.ids)], context=context)
            toc = toc_obj.browse(cr, uid, toc_ids_list, context=context)

        # Search again to honor user rights and access rules
        if post:
            post_obj = request.registry['forum.post']
            post_ids_list = post_obj.search(cr, uid, [('id', 'in', post.ids)], context=context)
            post = post_obj.browse(cr, uid, post_ids_list, context=context)

        if not post:
            return request.redirect("/")

        return super(WebsiteDocPrivate, self).post(toc=toc, post=post, **kwargs)
