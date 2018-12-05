# -*- coding: utf-'8' "-*-"
from openerp import http, fields
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

import json


class FSOEmailEditor(http.Controller):

    @http.route('/altruja/create/<int:spenden_id>', type='json', auth="user", website=True)
    def altruja_create(self, spenden_id, update_existing_record=False, **post):
        """
        Create a new record from the received data.
        HINT: Raises an exception if a record with this "spenden_id" exists already if "update_existing_record" is False!

        :param spenden_id: Int, This is used as the "external ID" of the record
        :param post: Dict, Dictionary from json data (fields of the altruja model)
        :return: Bool
        """
        assert int(spenden_id), "'spenden_id' not set on rest url or not an int! E.g.: /altruja/create/37652"
        assert post, "Payload of request is empty (post)!"

        altruja = http.request.env['altruja']

        # Check for non existing fields in **post!
        # ATTENTION: (f for f in) will create a generator! Use tuple(f for f in) instead!
        altruja_fields = tuple(name for name, field in altruja._fields.items())
        fields_not_in_model = tuple(f for f in post if f not in altruja_fields)
        assert not fields_not_in_model, "Unknown fields found: %s" % fields_not_in_model

        # Add spenden_id to post variables
        post["spenden_id"] = int(spenden_id)

        # Add current datetime to post (Log last change from controller)
        post["controller_update_date"] = fields.datetime.now()

        # UPDATE RECORD
        if update_existing_record:

            # Find record
            record = altruja.search([('spenden_id', '=', spenden_id)], limit=1)
            assert len(record) == 1, "Record not found with spenden_id %s" % spenden_id

            # Update record
            assert record.write(post), "Update of record failed!"
            return self.altruja_read(record=record)

        # CREATE RECORD
        record = altruja.create(post)
        return self.altruja_read(record=record)

    @http.route('/altruja/update/<int:spenden_id>', type='json', auth="user", website=True)
    def altruja_update(self, spenden_id, **post):
        """
        Update an existing record from the received data.

        :param spenden_id: Int, This is used as the "external ID" of the record
        :param post: Dict, Dictionary from json data (fields of the altruja model)
        :return: True or Exception
        """
        json_result = self.altruja_create(spenden_id=spenden_id, update_existing_record=True, **post)
        return json_result

    @http.route('/altruja/read/<int:spenden_id>', type='json', auth="user", website=True)
    def altruja_read(self, spenden_id=False, record=False, **post):
        """
        Return a dict with all fields of the record found by "spenden_id" !

        :param spenden_id:
        :param post:
        :return: dict, Returns all fields of the model 'altruja'
        """
        # Get/Check the record
        if not record:
            assert int(spenden_id), "'spenden_id' not set on rest url or not an int! e.g.: /altruja/create/37652"

            # Find record
            record = http.request.env['altruja'].search([('spenden_id', '=', spenden_id)], limit=1)
        assert record, "Record not found!"

        # Convert selected record-data to json
        # HINT: For security reasons we do not send information about the person or the bank account.
        record_data = {
            # FSON
            'id': record.id,
            'create_date': record.create_date,
            'write_date': record.write_date,
            'controller_update_date': record.controller_update_date,
            'state': record.state,
            'error_type': record.error_type,
            'error_details': record.error_details,
            # Altruja
            'spenden_id': record.spenden_id,
            'erstsspenden_id': record.erstsspenden_id,
            'datum': record.datum,
            'spenden_typ': record.spenden_typ,
            'spendenbetrag': record.spendenbetrag,
            'intervall': record.intervall,
            'waehrung': record.waehrung,
            'quelle': record.quelle,
        }
        #record_data_json = json.dumps(record_data)

        return record_data
