# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api

import logging
logger = logging.getLogger(__name__)


class ResPartnerFRSTSecurity(models.Model):
    _inherit = "res.partner"

    fson_sosync_user = fields.Boolean(string="Sosyncbenutzer", readonly=True)
    fson_system_user = fields.Boolean(string="Systembenutzer", readonly=True)
    fson_admin_user = fields.Boolean(string="Sachbearbeiter", readonly=True)
    fson_donor_user = fields.Boolean(string="Kunden-, Spenderbenutzer", readonly=True)

    @api.multi
    def compute_security_fields(self):
        logger.info("Compute security fields for %s res.partner" % (len(self) if self else 'all'))
        ref = self.env.ref

        def update_field(self, field_name, group_xml_ids):
            logger.info("Update field %s" % field_name)
            group_ids = [self.env.ref(xml_gid).id for xml_gid in group_xml_ids]

            set_domain = [('user_ids.groups_id', 'in', group_ids), (field_name, '=', False)]
            if self:
                set_domain += [('id', 'in', self.ids)]
            to_set = self.search(set_domain)
            to_set.write({field_name: True})
            logger.info("Set %s=True for %s records found by %s" % (field_name, len(to_set), set_domain))

            unset_domain = [('user_ids.groups_id', 'not in', group_ids), (field_name, '=', True)]
            if self:
                unset_domain += [('id', 'in', self.ids)]
            to_unset = self.search(unset_domain)
            to_unset.write({field_name: False})
            logger.info("Set %s=False for %s records found by %s" % (field_name, len(to_unset), unset_domain))

        update_field(self, 'fson_sosync_user', ['base.sosync'])
        update_field(self, 'fson_system_user', ['base.group_no_one', 'fso_base.instance_system_user', 'base.studio',
                                                'base.sosync'])
        update_field(self, 'fson_admin_user', ['base.group_user'])
        update_field(self, 'fson_donor_user', ['base.group_public'])

    @api.model
    def compute_security_fields_for_all_partner(self):
        self.compute_security_fields()


