# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api


class MailMessageSosync(models.Model):
    _name = "mail.message"
    _inherit = ["mail.message", "base.sosync"]

    type = fields.Selection(sosync="fson-to-frst")

    email_from = fields.Char(sosync="fson-to-frst")
    reply_to = fields.Char(sosync="fson-to-frst")
    author_id = fields.Many2one(sosync="fson-to-frst")
    partner_ids = fields.Many2many(sosync="fson-to-frst")
    notified_partner_ids = fields.Many2many(sosync="fson-to-frst")
    notification_ids = fields.One2many(sosync="fson-to-frst")

    parent_id = fields.Many2one(sosync="fson-to-frst")
    child_ids = fields.One2many(sosync="fson-to-frst")

    model = fields.Char(sosync="fson-to-frst")
    res_id = fields.Integer(sosync="fson-to-frst")
    record_name = fields.Char(sosync="fson-to-frst")

    message_id = fields.Char(sosync="fson-to-frst")
    date = fields.Datetime(sosync="fson-to-frst")

    subject = fields.Char(sosync="fson-to-frst")
    body = fields.Html(sosync="fson-to-frst")
    attachment_ids = fields.Many2many(sosync="fson-to-frst")

    subtype_id = fields.Many2one(sosync="fson-to-frst")
    subtype_xml_id = fields.Char(sosync="fson-to-frst")

    @api.multi
    def create_sync_job(self,
                        job_date=False,
                        sosync_write_date=False,
                        job_priority=False,
                        job_source_fields=False,
                        job_source_type=False,
                        job_source_merge_into_record_id=False,
                        job_source_target_merge_into_record_id=False):

        sync_job_messages = self
        # HINT: Maybe this if is not needed because this abstract-class-method-override is done for mail.message only?
        if self._name == "mail.message":
            sync_job_messages = self.filtered(lambda r: r.subtype_xml_id and
                                                        r.subtype_xml_id.startswith('fso_mail_message_subtypes'))

        return super(MailMessageSosync, sync_job_messages).create_sync_job(
            job_date=job_date,
            sosync_write_date=sosync_write_date,
            job_priority=job_priority,
            job_source_fields=job_source_fields,
            job_source_type=job_source_type,
            job_source_merge_into_record_id=job_source_merge_into_record_id,
            job_source_target_merge_into_record_id=job_source_target_merge_into_record_id)
