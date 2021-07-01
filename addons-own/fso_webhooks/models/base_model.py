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
    try:
        if not webhooks:
            return

        if not recordset or not hasattr(recordset, 'env') or not hasattr(recordset, '_name'):
            return

        target_model = recordset._name
        if not target_model or target_model == 'fson.webhook':
            return

        session = ConnectorSession.from_env(recordset.env)
        for webhook in webhooks:

            # Apply post update record-filter
            filtered_recordset = webhook._filter_records(recordset)

            # Create a connector job for each request
            if webhook.one_request_per_record:
                for r in filtered_recordset:
                    request_kwargs = webhook.request_kwargs(r)
                    fire.delay(session, recordset._name, webhook.id, request_kwargs, recordset_ids=recordset.ids)
            else:
                request_kwargs = webhook.request_kwargs(recordset)
                fire.delay(session, recordset._name, webhook.id, request_kwargs, recordset_ids=recordset.ids)

    except Exception as e:
        logger.error("fire_webhooks failed for %s, %s! %s" % (webhooks, recordset, repr(e)))
        pass


def search_for_webhooks(recordset, crud_method, append_domain=None):
    webhooks = dict()
    try:
        assert crud_method in ('create', 'write', 'unlink'), "unexpected crud_method %s" % crud_method

        if not recordset or not hasattr(recordset, 'env') or not hasattr(recordset, '_name'):
            return webhooks

        target_model = recordset._name
        if not target_model or target_model == 'fson.webhook' or target_model.startswith('ir.'):
            return webhooks

        # Search for webhooks
        w_domain = [('model_id.model', '=', target_model), ('on_'+crud_method, '=', True)]
        if append_domain:
            w_domain.append(append_domain)
        webhooks = recordset.env['fson.webhook'].sudo().search(w_domain)

    except Exception as e:
        logger.error("search_for_webhooks failed for %s, %s! %s" % (crud_method, recordset, repr(e)))
        pass

    return webhooks


def filter_recordsets_pre_update(webhooks, recordset):
    pre_update_recordsets = dict()
    try:
        if not webhooks or not recordset or not hasattr(recordset, 'env') or not hasattr(recordset, '_name'):
            return pre_update_recordsets

        for w in webhooks:
            if w.filter_domain_pre_update:
                pre_update_recordsets[w.id] = w._filter_records(recordset,
                                                                filter_domain_field='filter_domain_pre_update')
    except Exception as e:
        logger.error("filter_recordsets_pre_update failed for %s, %s! %s" % (webhooks, recordset, repr(e)))
        pass

    return pre_update_recordsets


# ------
# CREATE
# ------
create_original = models.BaseModel.create


@openerp.api.model
@openerp.api.returns('self', lambda value: value.id)
def create(self, vals):
    record_id = create_original(self, vals)
    webhooks = search_for_webhooks(record_id, 'create')
    fire_webhooks(webhooks, recordset=record_id)
    return record_id


models.BaseModel.create = create


# -----
# WRITE
# -----
write_original = models.BaseModel.write


@openerp.api.multi
def write(self, vals):
    webhooks = search_for_webhooks(self, 'write')
    pre_update_recordsets = filter_recordsets_pre_update(webhooks, self)

    # Update records
    result = write_original(self, vals)

    for w in webhooks:
        if w.id in pre_update_recordsets:
            fire_webhooks(w, recordset=pre_update_recordsets[w.id])
        elif not w.filter_domain_pre_update:
            fire_webhooks(w, recordset=self)
        else:
            logger.error("Webhook %s has a filter_domain_pre_update but could not be found in pre_update_recordsets!"
                         "" % w.id)

    return result


models.BaseModel.write = write


# ------
# UNLINK
# ------
unlink_original = models.BaseModel.unlink


@openerp.api.multi
def unlink(self):
    webhooks = search_for_webhooks(self, 'unlink')
    fire_webhooks(webhooks, recordset=self)
    return unlink_original(self)


models.BaseModel.unlink = unlink
