# -*- coding: utf-8 -*-

from openerp import api, models, fields


class View(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def save_embedded_field(self, el):
        context = self.env.context
        website = self.env['website'].sudo().browse([1])[0]
        en_us_lang_id = self.env['res.lang'].sudo().search([('code', '=', 'en_US')])[0].id

        # Ensure that en_US (English) is disabled for the website
        if en_us_lang_id not in website.language_ids.ids:
            # Check if the current language is the website-default-language
            if context.get('lang', False) == website.default_lang_id.code:
                context_temp = dict(context)
                context_temp.update({'lang': 'en_US'})
                super(View, self).with_context(context_temp).save_embedded_field(el)

        return super(View, self).save_embedded_field(el)
