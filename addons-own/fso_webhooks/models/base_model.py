# -*- encoding: utf-8 -*-
import openerp
from openerp import api, fields, models


# ------
# CREATE
# ------
create_original = models.BaseModel.create


@openerp.api.model
@openerp.api.returns('self', lambda value: value.id)
def create(self, vals):
    record_id = create_original(self, vals)
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.name', '=', self._name), ('on_create', '=', True)])
    if webhooks:
        webhooks.fire_webhooks(record_id)
    return record_id


models.BaseModel.create = create


# -----
# WRITE
# -----
write_original = models.BaseModel.write


@openerp.api.multi
def write(self, vals):
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.name', '=', self._name), ('on_write', '=', True)])
    if webhooks:
        # TODO: create recordsets for value_change candidates
        pass
    result = write_original(self, vals)
    if webhooks:
        # TODO: Fire webhooks for all records where a correct value change was detected
        pass
    return result


models.BaseModel.write = write


# ------
# UNLINK
# ------
unlink_original = models.BaseModel.unlink


@openerp.api.multi
def unlink(self):
    webhooks = self.env['fson.webhook'].sudo().search([('model_id.name', '=', self._name), ('on_unlink', '=', True)])
    if webhooks:
        webhooks.fire_webhooks(self)
    return unlink_original(self)


models.BaseModel.unlink = unlink
