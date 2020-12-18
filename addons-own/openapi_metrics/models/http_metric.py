# -*- coding: utf-8 -*-

from openerp import fields, models


class HttpMetric(models.Model):
    _name = "openapi.http_metric"
    _order = "create_date desc"
    _description = "OpenAPI HTTP Metric"
    _sql_constraints = [
        (
            'namespace_id_day_model_unique',
            'unique(namespace_id, day, model)',
            "Metrics for this integration, day and model already exist."
        ),
    ]

    namespace_id = fields.Integer(
        string="The OpenAPI Integration ID",
        readonly=True)

    namespace_name = fields.Char(
        string="The OpenAPI Integration name",
        readonly=True)

    day = fields.Datetime(
        string="Day of the request.",
        readonly=True)

    model = fields.Char(
        string="Model name",
        readonly=True)

    request_count = fields.Integer(
        string="Number of requests for the given day.",
        readonly=True)
