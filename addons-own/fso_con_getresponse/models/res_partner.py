# -*- coding: utf-8 -*-
from openerp import api, models


class ResPartnerGetResponse(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def button_open_getresponse_contact_bindings(self):
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

    @api.multi
    def button_open_getresponse_tag_bindings(self):
        assert self.ensure_one(), "Please select one partner only!"
        # HINT: This will not overwrite the domain of the view because we do not use action.domain =
        #       Maybe we should do a deepcopy and a convert to an dict to make this more obvious ;)
        action = self.env['ir.actions.act_window'].for_xml_id(
            'fso_con_getresponse', 'action_getresponse_gr_tag')
        action['domain'] = [('odoo_id.partner_ids.id', '=', self.id),
                            '|',
                                ('active', '=', False),
                                ('active', '=', True)
                            ]
        return action

    @api.multi
    def button_open_getresponse_jobs(self):
        assert self.ensure_one(), "Please select one partner only!"
        # HINT: This will not overwrite the domain of the view because we do not use action.domain =
        #       Maybe we should do a deepcopy and a convert to an dict to make this more obvious ;)

        # Contact Bindings
        contact_bindings = self.env['getresponse.frst.personemailgruppe'].search(
            [('odoo_id.frst_personemail_id.partner_id.id', '=', self.id),
             '|',
                ('active', '=', False),
                ('active', '=', True)
             ]
        )

        # Tag Bindings
        tag_bindings = self.env['getresponse.gr.tag'].search(
            [('odoo_id.partner_ids.id', '=', self.id),
             '|',
                ('active', '=', False),
                ('active', '=', True)
             ]
        )

        action = self.env['ir.actions.act_window'].for_xml_id('connector', 'action_queue_job')
        action['domain'] = ['|',
                                '&',
                                    ('binding_id', 'in', contact_bindings.ids),
                                    ('binding_model', '=', contact_bindings._name),
                                '&',
                                    ('binding_id', 'in', tag_bindings.ids),
                                    ('binding_model', '=', tag_bindings._name),
                            ]
        action['context'] = {}
        return action
