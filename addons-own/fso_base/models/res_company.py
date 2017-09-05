# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _


class CompanyInstanceSettings(models.Model):
    _inherit = 'res.company'

    instance_company = fields.Boolean(string='Instance Main Company')
    instance_base_port = fields.Char(string='Instance Base Port', size=5)
    instance_id = fields.Char(string='Instance ID (e.g.: dadi)', size=5)

    @api.model
    def _check_instance_company(self, vals):
        # Check if a new instance company is going to be set
        if vals.get("instance_company", False) and not (hasattr(self, "instance_company") and self.instance_company):

            # Make sure all fields are filled for the main instance company
            assert (all(vals.get(f) if f in vals else self[f] for f in ("instance_base_port", "instance_id"))), _(
                "'Instance Base Port' and 'Instance ID' must be set for the 'Instance Main Company'!")

            # Search for former instance companies
            domain = [("instance_company", "=", True)]
            if hasattr(self, "id") and self.id:
                domain += [("id", "!=", self.id)]
            former_comps = self.sudo().search(domain)

            # Unset instance fields of former main instance companies
            if former_comps:
                former_comps.write({"instance_company": False, "instance_base_port": False, "instance_id": False})

            # Return True since a new instance company is set with all relevant fields
            return True

        # Return False if no instance company was set
        return False

    @api.model
    def _update_instance_company_of_instance_user(self, instance_company=False):
        # Set main company for all users with the group fso_base.instance_system_user to the new instance company!
        instance_company = instance_company or self.sudo().search([("instance_company", "=", True)])
        instance_company.ensure_one()
        instance_system_user_group = self.env.ref("fso_base.instance_system_user")
        instance_system_users = instance_system_user_group.users
        for user in instance_system_users:
            # HINT: Do a direct write with = so the next write will not fail with a "company not allowed"
            user.company_ids = user.company_ids.ids + instance_company.ids
        if instance_system_users:
            instance_system_users.sudo().write({"company_id": instance_company.id})

    @api.model
    def create(self, vals, **kwargs):

        # Check main instance setting
        new_instance_company = self._check_instance_company(vals)

        # TODO: Add all instance-system-users to the vals
        # HINT: The stuff below is not jet working :(
        # instance_system_user_group = self.env.ref("fso_base.instance_system_user")
        # instance_system_users = instance_system_user_group.users
        # if instance_system_users:
        #     vals["user_ids"] = vals.get("user_ids", []) + instance_system_users.ids

        # Create the new company
        ret = super(CompanyInstanceSettings, self).create(vals, **kwargs)

        # Update main company of instance-system-users if this company is the new instance main company
        if new_instance_company:
            self._update_instance_company_of_instance_user()

        return ret

    @api.multi
    def write(self, vals, **kwargs):

        # Check main instance setting
        new_instance_company = self._check_instance_company(vals)

        # Update the company
        ret = super(CompanyInstanceSettings, self).write(vals, **kwargs)

        # Update main company of instance-system-users if this company is the new instance main company
        if new_instance_company:
            self._update_instance_company_of_instance_user()
        return ret


