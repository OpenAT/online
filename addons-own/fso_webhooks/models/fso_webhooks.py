# -*- coding: utf-8 -*-
import json

from requests import Session, codes
import ast
from urllib import urlencode, quote as quote
import datetime
import dateutil.relativedelta as relativedelta

from openerp import models, fields, api, tools
from openerp.tools.translate import _
from openerp.addons.email_template.email_template import format_tz
from openerp.exceptions import Warning

import logging
logger = logging.getLogger(__name__)

try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    jinja2_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=False,
    )
    jinja2_template_env.globals.update({
        'str': str,
        'quote': quote,
        'urlencode': urlencode,
        'datetime': tools.wrap_module(datetime, []),
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),

        'json_dumps': json.dumps,
    })
except ImportError:
    logger.warning("jinja2 not available, templating features will not work!")


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
                                           help="Conditions that must be met before an update to fire a webhook. \n"
                                                "(Records are filtered by this domain only before an update).")
    filter_domain = fields.Text(string="Filter Domain", help="Conditions that must be met to fire a webhook. \n"
                                                             "(Records are filtered by this domain after an create "
                                                             "or update or before an unlink)")

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

    @api.constrains('model_id')
    def constrain_model_id(self):
        for r in self:
            if r.model_id:
                assert not r.model_id.model.startswith('ir.'), "ir.* models are not allowed for webhooks!"

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
        payload_string_utf8 = payload_unicode.encode('utf-8')

        return payload_string_utf8

    @api.multi
    def request_kwargs(self, record):
        """ returns all data for the request """
        w = self
        w.ensure_one()

        request_kwargs = {
            'headers': {'content-type': w.content_type}
        }

        # Payload
        payload_string_utf8 = w.render_payload(record)
        if w.content_type == 'application/json; charset=utf-8':
            try:
                # Deserialize a string (or unicode) containing a json object to a python object to test if it
                # contains a valid json object
                payload_json = json.loads(payload_string_utf8, encoding='utf-8')
            except Exception as e:
                logger.error("Payload could not be converted to json! %s" % repr(e))
                raise e
            # HINT: request.post(json=...) will serialize a python object to a valid json string
            #
            # FROM DOC: Instead of encoding the dict (python object) yourself, you can also pass it directly using
            # the json parameter (added in version 2.4.2) and it will be encoded automatically. Note, the json
            # parameter is ignored if either data or files is passed. Using the json parameter in the request will
            # change the Content-Type in the header to application/json.
            #request_kwargs['json'] = payload_json
        # else:
        request_kwargs['data'] = payload_string_utf8

        return request_kwargs

    @api.multi
    def fire(self, request_kwargs):
        w = self
        w.ensure_one()
        tgt = w.target_id
        tgt.ensure_one()
        assert w.exists(), "Webhook %s no longer exits!" % w
        assert tgt.exists(), "Webhook target %s no longer exists!" % tgt
        assert isinstance(request_kwargs, dict), _("request_kwargs must be of type dict")
        assert isinstance(request_kwargs.get('headers', None), dict), _(
            "Key 'headers' missing in request_kwargs or not a dict!")

        session = Session()
        session.verify = True

        # Target
        request_kwargs['url'] = tgt.url

        # Target Authentication
        if tgt.auth_type == 'simple':
            session.auth = (tgt.user, tgt.password)
            if tgt.auth_header:
                request_kwargs['headers'][tgt.auth_header] = tgt.password
        elif tgt.auth_type == 'cert':
            session.cert = (tgt.crt_pem, tgt.crt_key)

        # Send request
        if w.http_type == 'POST':
            try:
                response = session.post(**request_kwargs)
                if response.status_code != codes.ok:
                    raise ValueError("Response status_code: %s, Response content: %s"
                                     "" % (response.status_code, response.content))
            except Exception as e:
                logger.error("Could not send webhook (id: %s)! request_kwargs: %s" % (w.id, request_kwargs))
                raise e
        else:
            raise NotImplementedError('Request type %s is not implemented!' % w.http_type)

        return response

    @api.multi
    def _filter_records(self, recordset, filter_domain_field='filter_domain'):
        self.ensure_one()

        filter_domain = ast.literal_eval(self[filter_domain_field]) if self[filter_domain_field] else False
        if not filter_domain:
            return recordset
        assert isinstance(filter_domain, list), "The domain in the field '%s' must be a list!" % filter_domain_field

        domain = [('id', 'in', recordset.ids)] + filter_domain
        filtered_recordset = recordset.search(domain)
        return filtered_recordset

    @api.multi
    def test_webhook_config(self):
        self.ensure_one()

        target_model_obj = self.env[self.model_id.model].sudo()

        try:
            # Test search domains
            for f in ('filter_domain_pre_update', 'filter_domain'):
                self._filter_records(target_model_obj, filter_domain_field=f)

            # Test kwargs (and therefore payload)
            record = target_model_obj.search([], limit=1)
            if not record:
                raise Warning(_("Can not test payload rendering because no record exists in target model!"))
            self.request_kwargs(record)
        except Exception as e:
            raise e

    @api.model
    def create(self, vals):
        record = super(FSONWebhooks, self).create(vals)
        record.test_webhook_config()
        return record

    @api.multi
    def write(self, vals):
        result = super(FSONWebhooks, self).write(vals)
        for r in self:
            r.test_webhook_config()
        return result
