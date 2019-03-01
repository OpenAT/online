# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

# import the base controller class to inherit from
from openerp.addons.website_forum.controllers.main import WebsiteForum


class WebsiteForumPrivate(WebsiteForum):

    @http.route()
    def questions(self, forum, tag=None, page=1, filters='all', sorting='date', search='', **post):
        cr, uid, context, = request.cr, request.uid, request.context

        # Search again to honor user rights and access rules
        if forum:
            forum_obj = request.registry['forum.forum']
            forum_id_list = forum_obj.search(cr, uid, [('id', 'in', forum.ids)], context=context)
            forum = forum_obj.browse(cr, uid, forum_id_list, context=context)
            if not forum:
                return request.redirect("/")

        return super(WebsiteForumPrivate, self).questions(forum,
                                                          tag=tag,
                                                          page=page,
                                                          filters=filters,
                                                          sorting=sorting,
                                                          search=search, **post)


