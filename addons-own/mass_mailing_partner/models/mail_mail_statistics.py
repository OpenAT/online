# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class MailMailStatistics(models.Model):
    _inherit = "mail.mail.statistics"

    personemail_id = fields.Many2one(comodel_name='frst.personemail', string="Person Email (FRST)")

    # Related field did not work for updates - therefore i try it now as a regular field
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner', readonly=True)

    @api.model
    def personemail_id_from_obj(self, model, res_id):
        personemail_id = False
        obj = self.env[model].browse(res_id)
        if obj.exists():
            if model == 'frst.personemail':
                personemail_id = res_id
            elif 'personemail_id' in obj._fields:
                personemail_id = obj.personemail_id.id
        return personemail_id

    @api.multi
    def personemail_link(self):
        for stat in self.filtered(lambda r: r.model and r.res_id):
            personemail_id = self.personemail_id_from_obj(stat.model, stat.res_id)
            if personemail_id != stat.personemail_id.id:
                stat.personemail_id = personemail_id
                if personemail_id:
                    stat.partner_id = self.env['frst.personemail'].sudo().browse([personemail_id]).partner_id.id
        return True

    @api.model
    def create(self, vals):
        stat = super(MailMailStatistics, self).create(vals)
        stat.personemail_link()
        return stat
