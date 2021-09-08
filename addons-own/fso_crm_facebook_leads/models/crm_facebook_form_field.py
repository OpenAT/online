# -*- coding: utf-8 -*-

from openerp import api, models, fields


class CrmFacebookFormField(models.Model):
    _inherit = 'crm.facebook.form.field'

    crm_field_type = fields.Selection(selection=[('', 'Standard'),
                                                 ('subscription', 'Group Subscription')])

    # For the crm_field_type 'subscription'
    # ------------------------------------
    # TODO: Constrains for the settings fields !!!
    zgruppedetail_id = fields.Many2one(string="Fundraising Studio Group",
                                       comodel_name="frst.zgruppedetail",
                                       inverse_name='crm_fb_form_field_ids',
                                       ondelete="set null", index=True,
                                       domain=[('zgruppe_id', '!=', False),
                                               ('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       help="Fundraising Studio E-Mail Group")
    # Subscription Group-Settings Overrides
    bestaetigung_erforderlich = fields.Boolean(string="Approval needed",
                                               default=False,
                                               help="If this checkbox is set gueltig_von and gueltig_bis will be set "
                                                    "to the past date 09.09.1999 when the group is created to indicate "
                                                    "that an approval is needed before set the group to active.")
    bestaetigung_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn'),
                                                   ('phone_call', "Phone Call"),
                                                   ('workflow', "Fundraising Studio Workflow"),
                                                   ],
                                        string="Approval Type", default='doubleoptin')
    bestaetigung_workflow = fields.Many2one(comodel_name="frst.workflow",
                                            inverse_name="approval_workflow_fb_field_ids",
                                            string="Approval Workflow",
                                            help="Fundraising Studio Approval Workflow")
    on_create_workflow = fields.Many2one(comodel_name="frst.workflow",
                                         inverse_name="on_create_workflow_fb_field_ids",
                                         string="On-Create Workflow",
                                         help="Fundraising Studio On-Create Workflow")

    # TODO: map contact_name to partner "name" field if contact_lastname is not used!!! on lead partner creation!
    # TODO: Choose a zGruppeDetail for the subscriptions! and Make sure PersonGruppe or PersonEmailGruppe will be set!
    # TODO: Choose the correct CDS Folder where the FRST Aktionen should be linked

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
