# -*- coding: utf-8 -*-
from openerp import api, models


class ResPartnerGetResponse(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def button_open_getresponse_bindings(self):
        assert self.ensure_one(), "Please select one partner only!"
        # HINT: This will not overwrite the domain of the view because we do not use action.domain =
        #       Maybe we should do a deepcopy and a convert to an dict to make this more obvious ;)
        action = self.env['ir.actions.act_window'].for_xml_id(
            'fso_con_getresponse', 'action_getresponse_frst_personemailgruppe')
        action['domain'] = [('odoo_id.frst_personemail_id.partner_id.id', '=', self.id),
                            '|',
                                ('active', '=', False),
                                ('active', '=', True)
                            ]
        return action
