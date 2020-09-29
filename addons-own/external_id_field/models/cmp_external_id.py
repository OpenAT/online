# -*- coding: utf-8 -*-
from openerp import models, api, fields
import re


class ExternalIdField(models.AbstractModel):
    """ This abstract model adds a computed field that will set or get the external id of the record in the target
        model (model that inherits from this). It is a convenience function to ease the creation of records where an
        external identifier is needed. It also makes it possible to search and

    """
    _name = "abstract.external_id"

    cmp_external_id = fields.Char(string="External ID", readonly=True)

    @api.model
    def create(self, vals):

        cmp_external_id = vals.get('cmp_external_id', None)

        # Test the cmp_external_id string
        if cmp_external_id:
            ext_id_model, ext_id_name = cmp_external_id.split('.')
            assert ext_id_model == self._model, "Model of cmp_external_id '{}' is not matching current model '{}'!" \
                                                "".format(ext_id_model, self._model)
            assert re.match(r"(?:[a-z0-9_]+)\Z", ext_id_name, flags=0), "Only a-z, 0-9 and _ is allowed in  " \
                                                                        "external_id name: '{}'".format(ext_id_name)

        res = super(ExternalIdField, self).create(vals)

        # Create the external id in odoo
        if res and cmp_external_id:
            assert not res.get_external_id(), "cmp_external_id {} given but resource '{} {}' has already an external " \
                                            "id '{}' after create!".format(cmp_external_id, res._model, res.id,
                                                                           res.cmp_external_id)
