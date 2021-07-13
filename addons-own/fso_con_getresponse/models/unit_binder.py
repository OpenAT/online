# -*- coding: utf-8 -*-
import copy
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
    def get_unbound(self, domain=None, limit=None):
        """ Get unwrapped records without a binding for this backend.
        ATTENTION: This method should be used to remove/filter out unwanted unbound records that should not get a
                   binding record at all (should not be exported)
        """
        domain = copy.deepcopy(domain) if domain else []
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

        # DISABLED: Because this takes way to much time
        # # Get all records bound to this backend
        # # HINT: If we test for a x2many field the test will return TRUE if it matches any (one or more) of the records
        # #       (this is just like any() in python)
        # bound_unwrapped_records_domain = [(backend_id_search_path, '=', backend_id)]
        # _logger.info("Search for bound_unwrapped_records: %s" % bound_unwrapped_records_domain)
        # bound_unwrapped_records = self.env[unwrapped_odoo_model].search(bound_unwrapped_records_domain)
        # _logger.info("Found %s bound_unwrapped_records" % len(bound_unwrapped_records))
        #
        # # Get all records without any binding or without any binding for the current backend
        # unbound_domain = domain + ['|',
        #                            (self._inverse_binding_ids_field, '=', False),
        #                            ('id', 'not in', bound_unwrapped_records.ids)
        #                            ]
        # _logger.info("Search for unbound_unwrapped_records: %s ..." % str(unbound_domain)[:1024])
        # unbound_unwrapped_records = self.env[unwrapped_odoo_model].search(unbound_domain, limit=limit)
        # _logger.info("Found %s unbound_unwrapped_records" % len(unbound_unwrapped_records))

        # Get unbound records (fast)
        # Example Domain:
        # exam = [
        #         ('zgruppedetail_id.sync_with_getresponse', '=', True),
        #         ('state', 'in', _sync_allowed_states),
        #         ('partner_frst_blocked', '=', False),
        #         ('partner_frst_blocked_email', '=', False),
        #         '|',
        #             (self._inverse_binding_ids_field, '=', False),
        #             '!', (backend_id_search_path, '=', backend_id),
        #         ]
        # Path to the backend id field of the bindings
        backend_id_search_path = self._inverse_binding_ids_field + '.' + self._backend_field + '.id'

        # Include records without any binding at all OR Include records if no binding exist for current backend
        # and append the given domain (which normally just excludes records based on states or Opt-Out fields)
        # get_unbound_domain = ['|',
        #                         (self._inverse_binding_ids_field, '=', False),
        #                         '!', (backend_id_search_path, '=', backend_id)]
        get_unbound_domain = [
            '|',
                '!', (self._inverse_binding_ids_field+'.active', '=', True),
                '!', '&', (self._inverse_binding_ids_field+'.active', '=', True),
                          (backend_id_search_path, '=', backend_id),
        ]
        get_unbound_domain += domain

        # Search for unbound records
        _logger.info("Search for unbound_unwrapped_records: %s" % str(get_unbound_domain)[:1024])
        unbound_unwrapped_records = self.env[unwrapped_odoo_model].search(get_unbound_domain, limit=limit)
        _logger.info("Found %s unbound records" % len(unbound_unwrapped_records))

        return unbound_unwrapped_records

    # PREPARE (CREATE) A NEW BINDING (BINDING WITHOUT AN EXTERNAL ID)
    def _prepare_binding(self, unwrapped_record_id, append_vals=None, connector_no_export=None):
        backend_id = self.backend_record.id
        binding_vals = {self._backend_field: backend_id,
                        self._openerp_field: unwrapped_record_id}

        if append_vals:
            assert isinstance(append_vals, dict), "'append_vals' must be a dict!"
            binding_vals.update(append_vals)

        # Delete deactivated bindings to avoid unique constraint errors
        inactive_bindings = self.model.search([(self._backend_field, '=', backend_id),
                                               (self._openerp_field, '=', unwrapped_record_id),
                                               ('active', '=', False)
                                               ])
        if inactive_bindings:
            unwrapped_odoo_model = self.unwrap_model()
            _logger.warning("Inactive bindings %s will be deleted for record %s %s before creating a new binding!" %
                            (inactive_bindings.ids, unwrapped_odoo_model, unwrapped_record_id))
            inactive_bindings.unlink()

        # Create the binding
        binding_model = self.model
        if connector_no_export:
            binding_model = self.model.with_context(connector_no_export=connector_no_export)
        prepared_binding_record = binding_model.create(binding_vals)

        _logger.info("Prepared binding record '%s', '%s'" % (prepared_binding_record._name, prepared_binding_record.id))

        return prepared_binding_record

    # CREATE BINDINGS FOR UNBOUND RECORDS
    def prepare_bindings(self, unbound_unwrapped_records=None, domain=None, append_vals=None, connector_no_export=None,
                         limit=None):
        """ Prepare (create) binding records for all unwrapped records without a binding record
        ATTENTION: This method must be used by all methods and consumer that prepare (create) binding records to make
                   sure the rules (domain) of get_unbound() are applied to filter out any invalid-unwrapped-records!

        ATTENTION: 'unbound_unwrapped_records' is deprecated! You can no longer force create a binding to avoid nasty
                   side effects! get_unbound() must be used to filter out all records that are not allowed to be
                   synced (e.g. blocked or deactivated records).

          domain: an odoo domain for the unwrapped odoo model that will be appended to the get_unbound() domain.
                  e.g.: domain=[('id', '=', unwrapped_record.id)]. If no domain is given get_unbound() will search
                  for all valid unbound records.
        """
        assert not unbound_unwrapped_records, "'unbound_unwrapped_records' is deprecated!"

        # Get unbound records based on the domain
        unbound_unwrapped_records = self.get_unbound(domain=domain, limit=limit)

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

    def get_bindings(self, domain=None, limit=None):
        """ Get all binding records for the current backend
        ATTENTION: This method must be used to validate the binding record for all exports!
                   Check unit_export.py _get_binding_record()
        """
        domain = domain if domain else []

        # Only search for bindings for the current backend
        backend_id = self.backend_record.id
        domain.append((self._backend_field, '=', backend_id))

        bindings = self.model.search(domain, limit=limit)
        return bindings
