# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from openerp import api, fields, models
from urllib2 import quote
from werkzeug import urls

class Namespace(models.Model):

    _inherit = "openapi.namespace"

    spec_editor_url = fields.Char("Specification Swagger-Editor", compute="_compute_editor_ui_url")
    spec_ui_url = fields.Char("Specification Swagger-UI", compute="_compute_editor_ui_url")

    @api.depends("name", "token")
    def _compute_editor_ui_url(self):
        for record in self:
            if record.spec_url:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

                full_spec_url = urls.url_join(base_url, record.spec_url)
                quoted_full_spec_url = quote(full_spec_url, safe="")

                ui_url_part = "/swagger-ui/index.html?swagger_spec_url={}".format(quoted_full_spec_url)
                editor_url_part = "/swagger-editor/index.html?swagger_spec_url={}".format(quoted_full_spec_url)

                record.spec_editor_url = urls.url_join(base_url, editor_url_part)
                record.spec_ui_url = urls.url_join(base_url, ui_url_part)
