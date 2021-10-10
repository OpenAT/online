# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.tools.translate import _


class CrmFacebookFormField(models.Model):
    _inherit = 'crm.facebook.form.field'

    # TODO: Link to zgruppedetail to select e-mail groups for subscription!
    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail",
                                       inverse_name='facebook_form_field_ids',
                                       string="Subscribe to E-Mail Group",
                                       domain=[('zgruppe_id', '!=', False),
                                               ('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       ondelete='set null')

    # TODO: map contact_name to partner "name" field if contact_lastname is not used!!! on lead partner creation!
    # TODO: Choose a zGruppeDetail for the subscriptions! and Make sure PersonGruppe or PersonEmailGruppe will be set!
    # TODO: Choose the correct CDS Folder where the FRST Aktionen should be linked

    @api.constrains('zgruppedetail_id', 'crm_field')
    def constrain_zgruppedetail_id_crm_field(self):
        for r in self:
            assert not (r.zgruppedetail_id and r.crm_field), _("You can not map a crm field and assign a "
                                                               "group subscription!")

    @api.constrains('zgruppedetail_id')
    def constrain_zgruppedetail_id(self):
        for r in self:
            if r.zgruppedetail_id:
                assert r.fb_field_type == "CONSENT_CHECKBOX", _("Only FB-Fields of type CONSENT_CHECKBOX can be used "
                                                                "to subscribe to additional e-mail groups")

    @api.model
    def facebook_field_type_to_odoo_field_name(self):

        # ATTENTION: super() always needs a second argument or it will return an unbound super object!
        #            https://stackoverflow.com/questions/26788214/super-and-staticmethod-interaction
        res = super(CrmFacebookFormField, self).facebook_field_type_to_odoo_field_name()

        # Append additional fields to the mapping
        # HINT: 'partner_' fields are for the company! 'contact_' fields for the person in crm.lead
        res.update({
            'FIRST_NAME': 'contact_name',
            'LAST_NAME': 'contact_lastname',
            'DOB': 'contact_birthdate_web',
        })

        return res
