# -*- encoding: utf-8 -*-
import openerp
from openerp import api, fields, models

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job

import logging
logger = logging.getLogger(__name__)


@job(default_channel='root.webhooks')
def fire(session, recordset_model, webhook_id, request_kwargs, **kwargs):
    webhook = session.env['fson.webhook'].browse([webhook_id])
    assert webhook.exists(), "Webhook with id %s no longer exists!" % webhook_id
    webhook.fire(request_kwargs)


def fire_webhooks(webhooks, recordset):
    session = ConnectorSession.from_env(recordset.env)
    for webhook in webhooks:

        # Apply post update record-filter
        filtered_recordset = webhook._filter_records(recordset)

        # Create a connector job for each request
        if webhook.one_request_per_record:
            for r in filtered_recordset:
                request_kwargs = webhook.request_kwargs(r)
                fire.delay(session, recordset._name, webhook.id, request_kwargs,
                           webhook_id=webhook.id, recordset_ids=recordset.ids)
        else:
            request_kwargs = webhook.request_kwargs(recordset)
            fire.delay(session, recordset._name, webhook.id, request_kwargs,
                       webhook_id=webhook.id, recordset_ids=recordset.ids)


# ------
# CREATE
# ------
create_original = models.BaseModel.create


@openerp.api.model
@openerp.api.returns('self', lambda value: value.id)
def create(self, vals):
    record_id = create_original(self, vals)

    webhooks = self.env['fson.webhook'].sudo().search([('model_id.model', '=', self._name), ('on_create', '=', True)])
    try:
        if webhooks:
            fire_webhooks(webhooks, record_id)
    except Exception as e:
        logger.error("Could not process webhooks for %s record create! %s" % (self._name, repr(e)))
        pass

    return record_id


models.BaseModel.create = create


# -----
# WRITE
# -----
write_original = models.BaseModel.write


@openerp.api.multi
def write(self, vals):
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.model', '=', self._name),
                                                       ('on_write', '=', True)])
    pre_update_recordsets = dict()

    try:
        if webhooks:
            for w in webhooks:
                if w.filter_domain_pre_update:
                    pre_update_recordsets[w.id] = w._filter_records(
                        self, filter_domain_field='filter_domain_pre_update')
    except Exception as e:
        logger.error("Could not apply filter_domain_pre_update for webhooks for %s record write! %s"
                     "" % (self._name, repr(e)))
        pass

    # Update records
    result = write_original(self, vals)

    try:
        if webhooks:
            for w in webhooks:
                if w.id in pre_update_recordsets:
                    fire_webhooks(w, pre_update_recordsets[w.id])
                else:
                    fire_webhooks(w, self)
    except Exception as e:
        logger.error("Could not process webhooks for %s record write! %s" % (self._name, repr(e)))
        pass

    return result


models.BaseModel.write = write


# ------
# UNLINK
# ------
unlink_original = models.BaseModel.unlink


@openerp.api.multi
def unlink(self):
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.model', '=', self._name), ('on_create', '=', True)])
    try:
        if webhooks:
            fire_webhooks(webhooks, self)
    except Exception as e:
        logger.error("Could not process webhooks for %s record unlink! %s" % (self._name, repr(e)))
        pass

    return unlink_original(self)


models.BaseModel.unlink = unlink
