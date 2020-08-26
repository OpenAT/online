# -*- coding: utf-8 -*-
from openerp import models
from openerp.addons.connector.connector import Binder
from .backend import getresponse

import json


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

    # ATTENTION: You must name all inverse fields of the '_openerp_field' like this!
    _inverse_openerp_field = 'getresponse_bind_ids'

    # ADD 'sync_data' TO THE BINDING METHOD AND BINDING RECORD
    def bind(self, external_id, binding_id, sync_data=None):
        # Call the original bind() method to write the sync_date field
        res = super(GetResponseBinder, self).bind(external_id=external_id, binding_id=binding_id)

        # If we got an id instead of an odoo record we load the odoo record right now
        if not isinstance(binding_id, models.BaseModel):
            binding_id = self.model.browse(binding_id)

        # Update 'sync_data' field of the binding record for comparison (concurrent write detection) at the next sync
        last_sync_data_json = json.dumps(sync_data, encoding='utf-8', ensure_ascii=False)
        binding_id.with_context(connector_no_export=True).write({'sync_data': last_sync_data_json})

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

        unwrapped_records = self.env[unwrapped_odoo_model].search(domain)

        # Get an empty recordset
        unbound_unwrapped_records = self.env[unwrapped_odoo_model]

        # Search for unbound records
        for r in unwrapped_records:
            binding_records = getattr(r, self._inverse_openerp_field)

            # No bindings at all or not binding for this backend
            if not binding_records or not any(binding.id == backend_id for binding in binding_records):
                unbound_unwrapped_records = unbound_unwrapped_records | r

        return unbound_unwrapped_records

    # PREPARE (CREATE) A NEW BINDING (BINDING WITHOUT AN EXTERNAL ID)
    def _prepare_binding(self, unwrapped_record_id):
        backend_id = self.backend_record.id
        binding_vals = {self._backend_field: backend_id,
                        self._openerp_field: unwrapped_record_id}
        prepared_binding_record = self.model.create(binding_vals)
        return prepared_binding_record

    # CREATE BINDINGS FOR UNBOUND RECORDS
    def prepare_bindings(self, unbound_unwrapped_records=None, domain=None):
        """ Prepare (create) binding records for all unwrapped records without a binding record
        ATTENTION: This method must be used by all methods and consumer that prepare (create) binding records!
        """
        # Get unbound records
        if not unbound_unwrapped_records:
            unbound_unwrapped_records = self.get_unbound(domain=domain)

        # Check the model of the recordset 'unbound_unwrapped_records'
        unwrapped_odoo_model = self.unwrap_model()
        assert unbound_unwrapped_records._name == unwrapped_odoo_model, (
                "unbound_unwrapped_records model must be %s" % unwrapped_odoo_model)

        # Prepare a binding for all unbound records
        prepared_bindings = self.env[self.model]
        for r in unbound_unwrapped_records:
            binding = self._prepare_binding(r.id)
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
