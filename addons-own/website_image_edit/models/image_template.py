# -*- coding: utf-8 -*-
import cStringIO
import datetime
from itertools import islice
import json
import xml.etree.ElementTree as ET

import logging
import re

import werkzeug.utils
import urllib2
import werkzeug.wrappers
from PIL import Image

import openerp
from openerp.addons.web.controllers.main import WebClient
from openerp.addons.web import http
from openerp.http import request, STATIC_CACHE
from openerp.tools import image_save_for_web

logger = logging.getLogger(__name__)

# Completely arbitrary limits
MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT = IMAGE_LIMITS = (1024, 768)
LOC_PER_SITEMAP = 45000
SITEMAP_CACHE_TIME = datetime.timedelta(hours=12)

class Website(openerp.addons.web.controllers.main.Home):

    @http.route('/website/attachTest', type='http', auth='user', methods=['POST'], website=True)
    def attach(self, func, upload=None, url=None, disable_optimization=None):
        Attachments = request.registry['ir.attachment']

        print('upload')
        print(upload)
        print(not upload)

        website_url = message = None
        if not upload:
            website_url = url
            name = url.split("/").pop()
            attachment_id = Attachments.create(request.cr, request.uid, {
                'name': name,
                'type': 'url',
                'url': url,
                'res_model': 'ir.ui.view',
            }, request.context)
            print('attachment id')
            print(attachment_id)
        else:
            try:
                image_data = upload.read()
                image = Image.open(cStringIO.StringIO(image_data))
                w, h = image.size
                if w*h > 42e6: # Nokia Lumia 1020 photo resolution
                    raise ValueError(
                        u"Image size excessive, uploaded images must be smaller "
                        u"than 42 million pixel")

                if not disable_optimization and image.format in ('PNG', 'JPEG'):
                    image_data = image_save_for_web(image)

                attachment_id = Attachments.create(request.cr, request.uid, {
                    'name': upload.filename,
                    'datas': image_data.encode('base64'),
                    'datas_fname': upload.filename,
                    'res_model': 'ir.ui.view',
                }, request.context)
                print('attachment id else')
                print(attachment_id)

                [attachment] = Attachments.read(
                    request.cr, request.uid, [attachment_id], ['website_url'],
                    context=request.context)
                website_url = attachment['website_url']
            except Exception, e:
                logger.exception("Failed to upload image to attachment")
                message = unicode(e)

        return """<script type='text/javascript'>
            window.parent['%s'](%s, %s);
        </script>""" % (func, json.dumps(website_url), json.dumps(message))
