# -*- coding: utf-8 -*-
# Copyright 2014 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2015 Grupo ESOC <www.grupoesoc.es>
# Copyright 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, fields, models
from . import exceptions


_logger = logging.getLogger(__name__)


class MailMassMailingContact(models.Model):
    """Adds last name and first name; name becomes a stored function field."""

    _inherit = 'mail.mass_mailing.contact'

    firstname = fields.Char("First name")
    lastname = fields.Char("Last name")
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True)

    @api.model
    def create(self, vals):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))

        if name is not None:
            # Calculate the splitted fields
            inverted = self._get_inverse_name(self._get_whitespace_cleaned_name(name))

            for key, value in inverted.iteritems():
                if not vals.get(key) or context.get("copy"):
                    vals[key] = value

            # Remove the combined fields
            if "name" in vals:
                del vals["name"]
            if "default_name" in context:
                del context["default_name"]

        return super(MailMassMailingContact, self.with_context(context)).create(vals)

    @api.multi
    def copy(self, default=None):
        """Ensure contacts are copied right.

        Odoo adds ``(copy)`` to the end of :attr:`~.name`, but that would get
        ignored in :meth:`~.create` because it also copies explicitly firstname
        and lastname fields.
        """
        return super(MailMassMailingContact, self.with_context(copy=True)).copy(default)

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(MailMassMailingContact, self).default_get(fields_list)

        inverted = self._get_inverse_name(self._get_whitespace_cleaned_name(result.get("name", "")))

        for field in inverted.keys():
            if field in fields_list:
                result[field] = inverted.get(field)

        return result

    @api.model
    def _names_order_default(self):
        return 'first_last'

    @api.model
    def _get_names_order(self):
        """Get names order configuration from system parameters.

        You can override this method to read configuration from language,
        country, company or other
        """
        return self.env['ir.config_parameter'].get_param(
            'partner_names_order', self._names_order_default())

    @api.model
    def _get_computed_name(self, lastname, firstname):
        """Compute the 'name' field according to splitted data.

        You can override this method to change the order of lastname and
        firstname the computed name
        """
        order = self._get_names_order()
        if order == 'last_first_comma':
            return u", ".join((p for p in (lastname, firstname) if p))
        elif order == 'first_last':
            return u" ".join((p for p in (firstname, lastname) if p))
        else:
            return u" ".join((p for p in (lastname, firstname) if p))

    @api.one
    @api.depends("firstname", "lastname")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        self.name = self._get_computed_name(self.lastname, self.firstname)

    @api.one
    def _inverse_name_after_cleaning_whitespace(self):
        """Clean whitespace in :attr:`~.name` and split it.

        The splitting logic is stored separately in :meth:`~._inverse_name`, so
        submodules can extend that method and get whitespace cleaning for free.
        """
        # Remove unneeded whitespace
        clean = self._get_whitespace_cleaned_name(self.name)

        # Clean name avoiding infinite recursion
        if self.name != clean:
            self.name = clean

        # Save name in the real fields
        else:
            self._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name, comma=False):
        """Remove redundant whitespace from :param:`name`.

        Removes leading, trailing and duplicated whitespace.
        """
        if name:
            name = u" ".join(name.split(None))
            if comma:
                name = name.replace(" ,", ",")
                name = name.replace(", ", ",")
        return name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        """Compute the inverted name.

        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes

        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """
        # Company name goes to the lastname
        if is_company or not name:
            parts = [name or False, False]
        # Guess name splitting
        else:
            order = self._get_names_order()
            # Remove redundant spaces
            name = self._get_whitespace_cleaned_name(
                name, comma=(order == 'last_first_comma'))
            parts = name.split("," if order == 'last_first_comma' else " ", 1)
            if len(parts) > 1:
                if order == 'first_last':
                    parts = [u" ".join(parts[1:]), parts[0]]
                else:
                    parts = [parts[0], u" ".join(parts[1:])]
            else:
                while len(parts) < 2:
                    parts.append(False)
        return {"lastname": parts[0], "firstname": parts[1]}

    @api.one
    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        parts = self._get_inverse_name(self.name)
        if parts["lastname"] != self.lastname:
            self.lastname = parts["lastname"]
        if parts["firstname"] != self.firstname:
            self.firstname = parts["firstname"]

    @api.one
    @api.constrains("firstname", "lastname")
    def _check_name(self):
        """Ensure at least one name is set."""
        if not (self.firstname or self.lastname):
            raise exceptions.EmptyNamesError(self)

    @api.one
    @api.onchange("firstname", "lastname")
    def _onchange_subnames(self):
        """Avoid recursion when the user changes one of these fields.

        This forces to skip the :attr:`~.name` inversion when the user is
        setting it in a not-inverted way.
        """
        # Modify self's context without creating a new Environment.
        # See https://github.com/odoo/odoo/issues/7472#issuecomment-119503916.
        self.env.context = self.with_context(skip_onchange=True).env.context

    @api.one
    @api.onchange("name")
    def _onchange_name(self):
        """Ensure :attr:`~.name` is inverted in the UI."""
        if self.env.context.get("skip_onchange"):
            # Do not skip next onchange
            self.env.context = (
                self.with_context(skip_onchange=False).env.context)
        else:
            self._inverse_name_after_cleaning_whitespace()

    @api.model
    def _install_contact_firstname(self):
        """Save names correctly in the database.

        Before installing the module, field ``name`` contains all full names.
        When installing it, this method parses those names and saves them
        correctly into the database. This can be called later too if needed.
        """
        # Find records with empty firstname and lastname
        records = self.search([("firstname", "=", False),
                               ("lastname", "=", False)])

        # Force calculations there
        records._inverse_name()
        _logger.info("%d mass mail list contacts updated installing module.", len(records))

    @api.multi
    def write(self, vals):
        name = vals.get('name')
        if name and all(name == r.name for r in self):
            vals.pop('name', None)
        # If vals is empty (only write name field and with the same value)
        # Avoid access checking here
        # https://github.com/odoo/odoo/blob/
        #   8b83119fad7ccae9f091f12b6ac89c2c31e4bac3/openerp/addons/base/res/
        #   res_partner.py#L569
        this = self.sudo() if not vals else self
        return super(MailMassMailingContact, this).write(vals)
