# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

from openerp import models
from openerp.addons.connector.connector import Binder
from .backend import getresponse

import json

_logger = logging.getLogger(__name__)


# HINT: Only use the @getresponse decorator on the class where you define _model_name but not on the parent classes!
class GetResponseBinder(Binder):
    # _model_name = [
    #     'getresponse.frst.zgruppedetail',               # Getresponse Campaigns
    #     'getresponse.gr.custom_field'                   # Getresponse Custom Field Definitions
    # ]

    # ATTENTION: This just uses the basic implementation of the binder - to make this work the fields names
    #            in the binding model must match the expected field names of the class 'Binder' OR tell the binder
    #            class the field names:
    _external_field = 'getresponse_id'
    _backend_field = 'backend_id'
    _openerp_field = 'odoo_id'
    _sync_date_field = 'sync_date'

    # WARNING: The _inverse_binding_ids_field name MUST be the same in all getresponse related binding models!
    #          You MUST name all inverse fields of the '_openerp_field' like this!
    _inverse_binding_ids_field = 'getresponse_bind_ids'

    # ADD 'sync_data' TO THE BINDING METHOD AND BINDING RECORD
    def bind(self, external_id, binding_id, sync_data=None, compare_data=None):
        # Call the original bind() method to write the sync_date field
        res = super(GetResponseBinder, self).bind(external_id=external_id, binding_id=binding_id)

        # If we got an id instead of an odoo record we load the odoo record right now
        if not isinstance(binding_id, models.BaseModel):
            binding_id = self.model.browse(binding_id)

        # Prepare 'sync_data'
        last_sync_data_json = json.dumps(sync_data, encoding='utf-8', ensure_ascii=False, default=str)

        # Prepare 'compare_data' (this is a GetResponse payload - created by the export mapper)
        compare_data_json = json.dumps(compare_data, encoding='utf-8', ensure_ascii=False, default=str)

        # Update the binding data (suppress exports on binding update with 'connector_no_export')
        binding_id.with_context(connector_no_export=True).write({'sync_data': last_sync_data_json,
                                                                 'compare_data': compare_data_json})

        return res

    # GET ALL UNWRAPPED RECORDS WITHOUT A BINDING FOR CURRENT BACKEND
    def get_unbound(self, domain=None):
        """ Get unwrapped records without a binding for this backend.
        ATTENTION: This method should be used to remove/filter out unwanted unbound records that should not get a
                   binding record at all (should not be exported)
        """
        domain = domain if domain else []
        unwrapped_odoo_model = self.unwrap_model()
        backend_id = self.backend_record.id

        # DISABLED: This was replaced by the domain below
        # TODO: We need to check if this is faster on large recordsets than the search below.
        #       I guessed the db search is faster and therefore i disabled this code.
        # # Get an empty recordset
        # unwrapped_records = self.env[unwrapped_odoo_model].search(domain)
        # unbound_unwrapped_records = self.env[unwrapped_odoo_model]
        #
        # # Search for records without a binding for this backend
        # backend_field = self._backend_field
        # for r in unwrapped_records:
        #     binding_records = getattr(r, self._inverse_binding_ids_field)
        #
        #     # No bindings at all or not binding for this backend
        #     if not binding_records or not any(
        #             getattr(binding, backend_field).id == backend_id for binding in binding_records):
        #         unbound_unwrapped_records = unbound_unwrapped_records | r

        # Path to the backend id field of the bindings
        backend_id_search_path = self._inverse_binding_ids_field + '.' + self._backend_field + '.id'

        # Get all records bound to this backend
        # HINT: If we test for a x2many field the test will return TRUE if it matches any of the records
        #       (this is just like any() in python)
        bound_unwrapped_records = self.env[unwrapped_odoo_model].search([(backend_id_search_path, '=', backend_id)])

        # Get all records without any binding or without any binding for the current backend
        domain += ['|',
                     (self._inverse_binding_ids_field, '=', False),
                     ('id', 'not in', bound_unwrapped_records.ids)
                   ]

        unbound_unwrapped_records = self.env[unwrapped_odoo_model].search(domain)
        return unbound_unwrapped_records

    # PREPARE (CREATE) A NEW BINDING (BINDING WITHOUT AN EXTERNAL ID)
    def _prepare_binding(self, unwrapped_record_id, append_vals=None, connector_no_export=None):
        backend_id = self.backend_record.id
        binding_vals = {self._backend_field: backend_id,
                        self._openerp_field: unwrapped_record_id}

        if append_vals:
            assert isinstance(append_vals, dict), "'append_vals' must be a dict!"
            binding_vals.update(append_vals)

        if connector_no_export:
            prepared_binding_record = self.model.with_context(
                connector_no_export=connector_no_export).create(binding_vals)
        else:
            prepared_binding_record = self.model.create(binding_vals)

        _logger.info("Prepared binding record '%s', '%s'" % (prepared_binding_record._name, prepared_binding_record.id))

        return prepared_binding_record

    # CREATE BINDINGS FOR UNBOUND RECORDS
    def prepare_bindings(self, unbound_unwrapped_records=None, domain=None, append_vals=None, connector_no_export=None):
        """ Prepare (create) binding records for all unwrapped records without a binding record
        ATTENTION: This method must be used by all methods and consumer that prepare (create) binding records!

        HINT: If you use unbound_unwrapped_records (recordset) instead of a domain the filters of get_unbound will not
              apply. This is like a 'force' prepare binding!

          domain: an odoo domain for the unwrapped odoo model
        """
        assert not (unbound_unwrapped_records and domain), "Use 'domain' or 'unbound_unwrapped_records' but not both!"
        # Get unbound records
        if not unbound_unwrapped_records:
            unbound_unwrapped_records = self.get_unbound(domain=domain)

        # Check the model of the recordset 'unbound_unwrapped_records'
        unwrapped_odoo_model = self.unwrap_model()
        assert unbound_unwrapped_records._name == unwrapped_odoo_model, (
                "unbound_unwrapped_records model must be %s" % unwrapped_odoo_model)

        # Prepare a binding for all unbound records
        prepared_bindings = self.env[self.model._name]
        for r in unbound_unwrapped_records:
            binding = self._prepare_binding(r.id, append_vals=append_vals, connector_no_export=connector_no_export)
            prepared_bindings = prepared_bindings | binding

        return prepared_bindings

    def get_bindings(self, domain=None):
        """ Get all binding records for the current backend
        ATTENTION: This method must be used to validate the binding record for all exports!
                   Check unit_export.py _get_binding_record()
        """
        domain = domain if domain else []

        # Only search for bindings for the current backend
        backend_id = self.backend_record.id
        domain.append((self._backend_field, '=', backend_id))

        bindings = self.model.search(domain)
        return bindings
