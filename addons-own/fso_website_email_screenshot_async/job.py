# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.queue.job import job


@job
def render_screenshot(session, template_id):
    # Make sure two jobs don't render the same e-mail template screenshot
    session.cr.execute(
        "SELECT id FROM email_template WHERE id = %s FOR UPDATE", (template_id,))

    # Make sure template still exists
    template = session.env['email.template'].browse(template_id)
    if not template.exists():
        return "email.template record (id=%s) no longer exists" % template_id

    # Render the Screenshot
    template.screenshot_update()


def queue_job(session, record_id, vals):
    kwargs = {}
    record = session.env['email.template'].browse(record_id)
    # if record.mail_job_priority:
    #     kwargs['priority'] = record.mail_job_priority
    render_screenshot.delay(session, record_id, **kwargs)


@on_record_create(model_names='email.template')
def template_creation(session, model_name, record_id, vals):
    if any(field in vals for field in
           ('body_html', 'fso_template_view_id', 'screenshot_pending')):
        if 'screenshot_pending' not in vals or vals.get('screenshot_pending', False):
            queue_job(session, record_id, vals)


@on_record_write(model_names='email.template')
def template_write(session, model_name, record_id, vals):
    if any(field in vals for field in
           ('body_html', 'fso_template_view_id', 'screenshot_pending')):
        if 'screenshot_pending' not in vals or vals.get('screenshot_pending', False):
            queue_job(session, record_id, vals)
