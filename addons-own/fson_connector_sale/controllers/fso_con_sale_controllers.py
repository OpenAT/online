# -*- coding: utf-'8' "-*-"
from openerp import http, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import ValidationError
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

import json


class FSOConSaleControllers(http.Controller):

    @http.route('/fson_connector_sale/create', type='json', auth="user", website=True)
    def fson_connector_sale_create(self, **post):
        assert post, "Payload of request is empty!"
        client_order_ref = post.get('client_order_ref')

        # Make sure only allowed fields are written!
        # ATTENTION: (f for f in) will create a generator! Use tuple(f for f in) instead!
        con_obj = http.request.env['fson.connector.sale']
        connector_fields = con_obj.get_fields_by_con_group('all')
        unknown_fields = tuple(f for f in post if f not in connector_fields)
        assert not unknown_fields, "Unknown fields found: %s" % str(unknown_fields)

        # Search for an existing record
        record = con_obj.search([('client_order_ref', '=', client_order_ref)], limit=2)
        assert len(record) <= 1, "More than one record found for client_order_ref %s !" % client_order_ref

        # TODO: Remove after updates are implemented
        assert not record, "This client_order_ref is already in use! The client_order_ref must be unique!"

        # Add additional data
        now = fields.datetime.now()
        now_string = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        data_log = now_string + ' data received:\n' + str(post) + '\n\n\n'
        post['received_data_date'] = now
        post['received_data_log'] = record.received_data_log + data_log if record else data_log

        # Create record
        if not record:
            _logger.info("Create fson.connector.sale record for client_order_ref %s" % client_order_ref)
            record = con_obj.create(post)

        # Update record
        else:
            _logger.info("Update fson.connector.sale record (id %s)" % str(record.id))
            record.write(post)

        # Return status
        assert record.state != 'error', "ERROR: %s" % record.error_details
        return {'client_order_ref': client_order_ref,
                'id': record.id,
                'state': record.state}
