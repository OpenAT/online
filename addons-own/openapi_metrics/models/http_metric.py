# -*- coding: utf-8 -*-

from openerp import fields, models


class HttpMetric(models.Model):
    _name = "openapi.http_metric"
    _order = "create_date desc"
    _description = "OpenAPI HTTP Metric"
    _sql_constraints = [
        ('day_unique', 'unique(day)', "Metrics for this day already exist."),
    ]

    day = fields.Datetime(
        string="Day of the response.",
        readonly=True)

    request_count = fields.Integer(
        string="Number of requests for the given day.",
        readonly=True)
