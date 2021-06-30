# -*- coding: utf-8 -*-
from requests import Session, codes
import ast

from openerp import models, fields, api, tools
from openerp.tools.translate import _
from openerp.addons.email_template.email_template import mako_template_env as jinja2_template_env, format_tz

import logging
logger = logging.getLogger(__name__)


class FSONWebhookTarget(models.Model):
    _name = "fson.webhook.target"
    _rec_name = "url"

    webhook_ids = fields.One2many(string="Webhooks", comodel_name='fson.webhook', inverse_name='target_id')

    url = fields.Char(string="URL", required=True)
    auth_type = fields.Selection(string="Authentification",
                                 selection=[('none', 'None'),
                                            ('simple', 'Simple / API-KEY'),
                                            ('cert', 'Certificate')
                                            ])
    # AUTH SECRETS
    user = fields.Char(string="User")
    auth_header = fields.Char(string="Auth header", help="If set will be added to the request-headers in the form"
                                                         "auth_header=password")
    password = fields.Char(string="API-Key or Password")
    # or
    crt_pem = fields.Binary(string="SSL-Cert (PEM)")
    crt_key = fields.Binary(string="SSL-Cert-Key (PEM)")

    timeout = fields.Integer(string="Timeout in seconds", required=True, default=10)

    @api.constrains('auth_type', 'user', 'password', 'crt_pem', 'crt_key')
    def constrain_auth_type(self):
        for r in self:
            if r.auth_type == 'simple':
                assert r.password, "password must be set for auth type 'simple'!"
            elif r.auth_type == 'cert':
                assert r.crt_key and r.crt_pem, "Certificate and Certificate-Key must be set for auth type 'cert'"


class FSONWebhooks(models.Model):
    _name = "fson.webhook"

    name = fields.Char('Name', required=True)
    model_id = fields.Many2one(string="Model", comodel_name="ir.model", required=True)
    description = fields.Text(string='Description')

    # TRIGGER (FIRE WEBHOOK ON)
    on_create = fields.Boolean("On Create")
    on_write = fields.Boolean("On Write")
    on_unlink = fields.Boolean("On Delete")

    # FILTER
    filter_domain_pre_update = fields.Text(string="Filter Domain before update",
                                           help="Records are filtered by this domain only before a write (update).")
    filter_domain = fields.Text(string="Filter Domain", help="Records are filtered by this domain after an create "
                                                             "or update or before an unlink")

    # REQUEST
    target_id = fields.Many2one(string="Request Target",
                                comodel_name='fson.webhook.target', inverse_name='webhook_ids',
                                required=True)
    http_type = fields.Selection(string="Request Type",
                                 selection=[('POST', 'POST')],
                                 default='POST', required=True)
    content_type = fields.Selection(string="Content Type",
                                    selection=[('application/json; charset=utf-8',
                                               'application/json; charset=utf-8')],
                                    default='application/json; charset=utf-8', required=True)
    one_request_per_record = fields.Boolean(string="One Request per Record", default=True,
                                            help="If NOT set only one request would be send for multiple records."
                                                 "This means you need to expect a record set in the payload instead of"
                                                 "a single record")
    req_payload = fields.Text(string="Payload",
                              help="Payload (body) of the request. Jinja 2 template can be used just like in "
                                   "e-mail templates")

    # TODO: Add onchange for on_val_change to set on_write to true and test by constrain
    @api.onchange('filter_domain_pre_update', 'on_write')
    def onchange_filter_domain_pre_update(self):
        for r in self:
            if r.filter_domain_pre_update:
                r.on_write = True

    @api.constrains('filter_domain_pre_update', 'on_write')
    def constrain_filter_domain_pre_update(self):
        for r in self:
            if r.filter_domain_pre_update:
                assert r.on_write, _("Trigger 'on_write' must bes set if pre update filter is set or pre-update-filter"
                                     "would have no effect!")

    @api.model
    def render_payload(self, recordset, post_process=False):
        w = self
        w.ensure_one()

        # Prepare template variables
        # HINT: Check mako_template_env() for jinja2 globals for all available python functions
        template_vars = {
            'object': recordset,
            'user': self.env.user,
            'ctx': self.env.context,
            'format_tz': lambda dt, tz=False, format=False, context=self.env.context: format_tz(
                self.pool, self.env.cr, self.env.uid, dt, tz, format, context),
        }

        # Load template
        try:
            jinja2_template = jinja2_template_env.from_string(tools.ustr(w.req_payload))
        except Exception as e:
            logger.error("Could not load jinja2 payload-template for webhook (id %s)! %s" % (w.id, repr(e)))
            raise e

        # Render template
        try:
            payload_unicode = jinja2_template.render(template_vars)
        except Exception as e:
            logger.error("Could not render jinja2 payload-template for webhook (id %s)! %s" % (w.id, repr(e)))
            raise e

        # Replace relative urls with absolute urls
        if post_process:
            payload_unicode = self.env['email.template'].render_post_process(result=payload_unicode)

        # Encode to utf8
        payload = payload_unicode.encode('utf-8')

        return payload

    @api.multi
    def fire(self, payload):
        w = self
        w.ensure_one()
        tgt = w.target_id

        session = Session()
        session.verify = True

        # Authentication
        headers = {}
        if tgt.auth_type == 'simple':
            session.auth = (tgt.user, tgt.password)
            if tgt.auth_header:
                headers[tgt.auth_header] = tgt.password
        elif tgt.auth_type == 'cert':
            session.cert = (tgt.crt_pem, tgt.crt_key)

        # Send request
        if w.http_type == 'POST':
            try:
                headers['content-type'] = w.content_type
                response = session.post(tgt.url,
                                        data=payload,
                                        headers=headers,
                                        timeout=tgt.timeout)
                if response.status_code != codes.ok:
                    raise ValueError("Response status_code: %s, Response content: %s"
                                     "" % (response.status_code, response.content))
            except Exception as e:
                logger.error("Could not send webhook (id %s) to %s with payload %s! %s"
                             "" % (w.id, tgt.url, payload, repr(e)))
                raise e
        else:
            raise NotImplementedError('Request type %s is not implemented!' % w.http_type)

        return response

    @api.multi
    def _filter_records(self, recordset, filter_domain_field='filter_domain'):
        self.ensure_one()

        filter_domain = ast.literal_eval(self[filter_domain_field])
        if not filter_domain:
            return recordset
        assert isinstance(filter_domain, list), "The domain in the field '%s' must be a list!" % filter_domain_field

        domain = [('id', 'in', recordset.ids)] + filter_domain
        filtered_recordset = recordset.search(domain)
        return filtered_recordset

    @api.multi
    def fire_webhooks(self, recordset):
        for webhook in self:
            filtered_recordset = webhook._filter_records(recordset)

            if webhook.one_request_per_record:
                for record in filtered_recordset:
                    payload = webhook.render_payload(record)
                    webhook.fire(payload=payload)
            else:
                payload = webhook.render_payload(filtered_recordset)
                webhook.fire(payload=payload)
