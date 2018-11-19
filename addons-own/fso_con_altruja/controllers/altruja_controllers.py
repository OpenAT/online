# -*- coding: utf-'8' "-*-"
from openerp import http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

import json


class FSOEmailEditor(http.Controller):

    @http.route('/altruja/create/<int:spenden_id>', type='json', auth="user", website=True)
    def altruja_create(self, spenden_id, update_existing_record=False, **post):
        """
        Create a new record from the received data.
        Raises an exception if a record with this "spenden_id" exists already if "update_existing_record" is False!
        :param spenden_id:
        :param post:
        :return: True or Exception
        """
        altruja = http.request.env['altruja']

        # Check for non existing fields in **post!
        # ATTENTION: (f for f in) will create a generator! Use tuple(f for f in) instead!
        altruja_fields = tuple(name for name, field in altruja._fields.items())
        fields_not_in_model = tuple(f for f in post if f not in altruja_fields)
        assert not fields_not_in_model, "Unknown fields found: %s" % fields_not_in_model

        # Update record
        if update_existing_record:
            result = self.altruja_update(spenden_id=spenden_id, **post)

        # Create record
        else:
            result = altruja.create(post)

        return result

    @http.route('/altruja/update/<int:spenden_id>', type='json', auth="user", website=True)
    def altruja_update(self, spenden_id, **post):
        """
        Update an existing record from the received data.
        Raises an exception if a record with this "spenden_id" exists already!
        :param spenden_id:
        :param post:
        :return: True or Exception
        """
        altruja = http.request.env['altruja']

        # Find record
        record = altruja.search([('spenden_id', '=', spenden_id)], limit=1)
        assert len(record) == 1, "Record not found with spenden_id %s" % spenden_id

        # Update record
        result = altruja.write(post)

        return result

    @http.route('/altruja/read/<int:spenden_id>', type='json', auth="user", website=True)
    def altruja_read(self, spenden_id, **post):
        """
        Return a dict with all fields of the record found by "spenden_id" !
        Raises an exception if the record is not found!
        :param spenden_id:
        :param post:
        :return: dict, Returns all fields of the model 'altruja'
        """
        record = http.request.env['altruja'].search([('spenden_id', '=', spenden_id)], limit=2)

        return True

    @http.route('/altruja/read/bulk', type='json', auth="user", website=True)
    def altruja_read_bulk(self, list_of_spenden_ids=(), **post):
        """
        Return a dict with all fields of the record found by "spenden_id" !
        Raises an exception if the record is not found!
        :param spenden_ids: tuple with id's
        :param post:
        :return: dict, Returns all fields of the model 'altruja'
        """
        list_of_spenden_ids = tuple(list_of_spenden_ids)
        assert list_of_spenden_ids, "Parameter 'list_of_spenden_ids' is empty!"

        return True
