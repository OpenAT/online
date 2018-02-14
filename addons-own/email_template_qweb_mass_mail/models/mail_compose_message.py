# -*- coding: utf-8 -*-
from openerp import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def render_message_batch(self, wizard, res_ids):
        """ render qweb template instead of jinja2 in mass_mail mode """
        res = super(MailComposeMessage, self).render_message_batch(wizard, res_ids)
        self.render_qweb_template_instead_of_jinja2(res, wizard, res_ids)
        return res

    def render_qweb_template_instead_of_jinja2(self, res, wizard, res_ids):
        if wizard.template_id.body_type == 'qweb':
            template_values = self.generate_email_for_composer_batch(wizard.template_id.id, res_ids, fields=['body_html'])
            for res_id in res_ids:
                res[res_id].update(template_values.get(res_id))

    def onchange_template_id(self, cr, uid, ids, template_id, composition_mode, model, res_id, context=None):
        """ mass_mailing: return qweb template instead of jinja2 if qweb used """
        res = super(mail_compose_message, self).onchange_template_id(cr, uid, ids, template_id, composition_mode, model, res_id, context=context)
        if template_id and composition_mode == 'mass_mail':
            template = self.pool['email.template'].browse(cr, uid, template_id, context=context)
            if template.body_type == 'qweb':
                res['value']['body'] = template.body_view_arch
        return res
