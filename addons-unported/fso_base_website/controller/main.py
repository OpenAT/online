# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

import logging
logger = logging.getLogger(__name__)

from openerp.addons.website.controllers.main import Website


class WebsiteFsoBase(Website):

    # Overwrite original robots controller ('/robots.txt') to use our template and because of 'noupdate' in our xml!
    @http.route()
    def robots(self, **kwargs):
        logger.info("Rendering alternative robots.txt from fso_base_website!")
        cr, uid, context = request.cr, request.uid, request.context

        website_id = request.registry['website'].search(cr, uid, [], limit=1, context=context)
        website = request.registry['website'].browse(cr, uid, website_id[0], context=context)

        return request.render('fso_base_website.robots_txt_template',
                              {'url_root': request.httprequest.url_root,
                               'robots_txt': website.robots_txt if website else '',
                               },
                              mimetype='text/plain')
