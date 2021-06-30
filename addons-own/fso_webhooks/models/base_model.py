# -*- encoding: utf-8 -*-
import openerp
from openerp import api, fields, models

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


# Function for Job Creation
@job(default_channel='root.webhooks')
def fire_webhooks_job(session, recordset_model, recordset_ids, webhook_ids):
    webhooks = session.env['fson.webhook'].browse(webhook_ids)
    recordset = session.env[recordset_model].browse(recordset_ids)
    webhooks.fire_webhooks(recordset)


# ------
# CREATE
# ------
create_original = models.BaseModel.create


@openerp.api.model
@openerp.api.returns('self', lambda value: value.id)
def create(self, vals):
    record_id = create_original(self, vals)
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.model', '=', self._name), ('on_create', '=', True)])
    if webhooks:
        session = ConnectorSession.from_env(self.env)
        fire_webhooks_job.delay(session, record_id._name, record_id.ids, webhooks.ids)
    return record_id


models.BaseModel.create = create


# -----
# WRITE
# -----
write_original = models.BaseModel.write


@openerp.api.multi
def write(self, vals):
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.model', '=', self._name), ('on_write', '=', True)])

    # Create a recordset for every webhook with a pre-update-filter
    pre_update_recordsets = dict()
    if webhooks:
        for w in webhooks:
            if w.filter_domain_pre_update:
                pre_update_recordsets[w.id] = w._filter_records(self, filter_domain_field='filter_domain_pre_update')

    # Update records
    result = write_original(self, vals)

    # Fire webhooks
    # HINT: The post update filter is done in fire_webhooks()!
    if webhooks:
        session = ConnectorSession.from_env(self.env)
        for w in webhooks:
            if w.id in pre_update_recordsets:
                pre_update_recordset = pre_update_recordsets[w.id]
                fire_webhooks_job.delay(session, pre_update_recordset._name, pre_update_recordset.ids, w.ids)
            else:
                fire_webhooks_job.delay(session, self._name, self.ids, w.ids)
    return result


models.BaseModel.write = write


# ------
# UNLINK
# ------
unlink_original = models.BaseModel.unlink


@openerp.api.multi
def unlink(self):
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.model', '=', self._name), ('on_unlink', '=', True)])
    filtered_recordset = webhooks._filter_records(self)
    # TODO: Unlink webhooks must be pre-rendered and to send them AFTER the unlink is done!
    if webhooks and filtered_recordset:
        session = ConnectorSession.from_env(self.env)
        fire_webhooks_job.delay(session, filtered_recordset._name, filtered_recordset.ids, webhooks.ids)
    return unlink_original(self)


models.BaseModel.unlink = unlink
