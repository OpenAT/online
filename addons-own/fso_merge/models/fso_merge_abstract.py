# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import mute_logger

import psycopg2

import logging
logger = logging.getLogger(__name__)


class FSOMergeAbstract(models.AbstractModel):
    _name = "fso.merge"

    # TODO: We skipped all the arguments in cr.execute because we directly inserted it in the query.
    #       Therefore we need to check if the escaping and '' or "" is ok for the postgres sql

    @staticmethod
    def _query_select_foreign_keys(table_name=''):
        return """  SELECT cl1.relname as table,
                           att1.attname as column
                      FROM pg_constraint as con, pg_class as cl1, pg_class as cl2,
                           pg_attribute as att1, pg_attribute as att2
                     WHERE con.conrelid = cl1.oid
                       AND con.confrelid = cl2.oid
                       AND array_lower(con.conkey, 1) = 1
                       AND con.conkey[1] = att1.attnum
                       AND att1.attrelid = cl1.oid
                       AND cl2.relname = '%s'
                       AND att2.attname = 'id'
                       AND array_lower(con.confkey, 1) = 1
                       AND con.confkey[1] = att2.attnum
                       AND att2.attrelid = cl2.oid
                       AND con.contype = 'f'
        """ % table_name

    @staticmethod
    def _query_select_all_columns(table_name=''):
        return """  SELECT column_name 
                      FROM information_schema.columns 
                     WHERE table_name LIKE '%s'
        """ % table_name

    @staticmethod
    def _query_update_fk_rel_table(keep_id=None, remove_id=None, table='', fk_column='', other_column=''):
        return """
                    UPDATE "%(table)s" as ___tu
                    SET %(fk_column)s = %(keep_id)s
                    WHERE
                        %(fk_column)s = %(remove_id)s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                %(fk_column)s = %(keep_id)s AND
                                ___tu.%(other_column)s = ___tw.%(other_column)s
                        )        
        """ % {'keep_id': keep_id, 'remove_id': remove_id,
               'table': table, 'fk_column': fk_column, 'other_column': other_column}

    @staticmethod
    def _query_update_fk(keep_id=None, remove_id=None, table='', fk_column=''):
        return """
                    UPDATE "%(table)s" 
                        SET %(fk_column)s = %(keep_id)s 
                      WHERE %(fk_column)s = %(remove_id)s
        """ % {'keep_id': keep_id, 'remove_id': remove_id, 'table': table, 'fk_column': fk_column}

    @staticmethod
    def _query_delete_records_linked_to_fk(table='', fk_column='', remove_id=''):
        return """
                    DELETE 
                      FROM %(table)s 
                     WHERE %(fk_column)s = %(remove_id)s
        """ % {'table': table, 'fk_column': fk_column, 'remove_id': remove_id}

    @api.model
    def _fso_merge_update_foreign_keys(self, rec_to_remove=None, rec_to_keep=None):
        logger.info("FSO MERGE: Update foreign keys")
        cr = self.env.cr

        merge_model_table = self._table

        # Loop through all tables with foreign key constraints/relations to the merge_model
        cr.execute(self._query_select_foreign_keys(table_name=merge_model_table))
        for fk_table, fk_column in cr.fetchall():

            # Get all other columns for this table
            cr.execute(self._query_select_all_columns(table_name=fk_table))
            other_columns = []
            for data in cr.fetchall():
                if data[0] != fk_column:
                    other_columns.append(data[0])

            # UPDATE FOR THE SPECIAL ODOO RELATION TABLES
            if len(other_columns) <= 1:
                # Update keys in the foreign key columns
                update_fk_rel_query = self._query_update_fk_rel_table(
                    keep_id=rec_to_keep.id, remove_id=rec_to_remove.id, table=fk_table, fk_column=fk_column,
                    other_column=other_columns[0])
                logger.info("FSO MERGE: Foreign key update for odoo-rel-table:\n%s"
                            "" % update_fk_rel_query.strip())
                cr.execute(update_fk_rel_query)

            # UPDATE FOR REGULAR ODOO MODEL-TABLES
            else:
                try:
                    # This will create a savepoint that i guess will be rolled back to by the orm if the stuff inside
                    # the 'with' throws an exception?
                    with mute_logger('openerp.sql_db'), cr.savepoint():
                        update_fk_query = self._query_update_fk(
                            keep_id=rec_to_keep.id, remove_id=rec_to_remove.id, table=fk_table, fk_column=fk_column)
                        logger.info("FSO MERGE: Foreign key update for regular-odoo-table:\n%s"
                                    "" % update_fk_query.strip())
                        cr.execute(update_fk_query)

                        # ATTENTION: There is no handling if the model has a relation to itself e.g. parent and child
                        #            If you need this add it like in crm base_partner_merge()
                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record linked to nonexistent record is useless, better delete it
                    delete_records_linked_to_fk_query = self._query_delete_records_linked_to_fk(
                        table=fk_table, fk_column=fk_column, remove_id=rec_to_remove.id)
                    logger.error("FSO MERGE: Update failed for regular table records! Keeping record linked to "
                                 "nonexistent record is useless, better delete it:"
                                 "\n%s" % delete_records_linked_to_fk_query.strip())
                    cr.execute(delete_records_linked_to_fk_query)

    @api.model
    def _update_rel_records(self, model_to_update='', mtu_fn_rel_model='model', mtu_fn_rel_id='res_id',
                            rel_model='frst.personemail', rel_rec_keep_id=None, rel_rec_remove_id=None):
        """
        This method is intended to update models with special relations. These relations consist of two fields
        in the model_to_update that hold the relation model name and the related record id.
        E.g.: in 'ir.attachments' are the fields 'res_model' (char) and 'res_id' (int) that can hold a relation to
        any model in odoo with just these two fields. This is an alternative implementation to avoid a dedicated m2o
        field for any model that needs to be linked.

        WARNING: Sometimes a third field (e.g.: 'res_name') is also in the model_to_update. This is no problem if the
                 field is updated automatically when the res_id or res_model field changes! Just make sure
                 to check if it is.

        :param model_to_update: model_to_update - The model where we need to update some fields
        :param mtu_fn_rel_model: Field-name containing the related-model-name in the model_to_update
        :param mtu_fn_rel_id: Field-name containing the related-record-id in the  model_to_update
        :param rel_model: Name of the related model
        :param keep_id: ID of the related record that will be kept (destination)
        :param remove_id: ID of the related record that will be removed/exchanged (source)
        :return:
        """
        cr = self.env.cr

        # Get the update model object as SUPERUSER
        try:
            update_model_obj = self.env[model_to_update].sudo()
        except KeyError:
            update_model_obj = None
        if update_model_obj is None:
            return

        # Find all records where the related record must be changed
        domain = [(mtu_fn_rel_model, '=', rel_model), (mtu_fn_rel_id, '=', rel_rec_remove_id)]
        records_to_update = update_model_obj.search(domain)

        # Update the records
        logger.info("FSO MERGE: Update the special-rel-field '%s' in the model '%s' to the value: %s"
                    "" % (mtu_fn_rel_id, records_to_update._name, rel_rec_keep_id))
        try:
            with mute_logger('openerp.sql_db'), cr.savepoint():
                return records_to_update.write({mtu_fn_rel_id: rel_rec_keep_id})
        except psycopg2.Error:
            logger.error("FSO MERGE: Update failed for special-rel-field records %s! Keeping records linked to "
                         "a nonexistent record is useless, better delete them." % records_to_update.ids)
            return records_to_update.unlink()

    @staticmethod
    def _fso_merge_special_reference_models():
        """
        Returns a list of tuples for models with special / old style reference fields
        (model_to_update, Field-Name containing the related-model-name, Field-Name containing the related-record-id)
        :return:
        """
        ref_models = [
            ('calendar', 'model_id.model', 'res_id'),
            ('ir.attachment', 'res_model', 'res_id'),
            ('mail.followers', 'res_model', 'res_id'),
            ('mail.message', 'model', 'res_id'),
            ('marketing.campaign.workitem', 'object_id.model', 'res_id'),
            ('ir.model.data', 'model', 'res_id'),
        ]
        return ref_models

    @api.model
    def _fso_merge_update_reference_fields(self, rec_to_remove=None, rec_to_keep=None):

        # UPDATE THE RECORD-ID IN ALL SPECIAL-REFERENCE-MODELS
        logger.info("FSO MERGE: Update special/oldstyle reference fields")
        for ref_mod in self._fso_merge_special_reference_models():
            self._update_rel_records(
                model_to_update=ref_mod[0], mtu_fn_rel_model=ref_mod[1], mtu_fn_rel_id=ref_mod[2],
                rel_model=self._name, rel_rec_keep_id=rec_to_keep.id, rel_rec_remove_id=rec_to_remove.id)

        # UPDATE THE RECORD-ID IN 'ir.model.fields' OF TYPE 'reference'
        logger.info("FSO MERGE: Update values of 'reference' fields found in 'ir.model.fields'")
        irmf_obj = self.env['ir.model.fields'].sudo()

        # Search in all 'reference' fields for the current model and record-to-remove-id
        irmf_rel_fields = irmf_obj.search([('ttype', '=', 'reference')])
        logger.info("FSO MERGE: Found %s fields of type 'reference'" % len(irmf_rel_fields))

        for irmf_field in irmf_rel_fields:
            try:
                target_model_obj = self.env[irmf_field.model].sudo()
                target_model_field = target_model_obj._fields[irmf_field.name]
            except KeyError:
                # Unknown model or field => skip
                continue

            # Skipp computed fields
            if target_model_field.compute is not None or isinstance(target_model_field.column, fields.fields.function):
                continue

            # Update the rel field
            domain = [(irmf_field.name, '=', '%s,%d' % (self._name, rec_to_remove.id))]
            target_model_records_to_update = target_model_obj.search(domain)
            if target_model_records_to_update:
                logger.info("FSO MERGE: Found %s records for reference-field '%s' in the model '%s' by domain: '%s'"
                            "" % (len(target_model_records_to_update), irmf_field.name, target_model_obj._name, domain))
                logger.info("FSO MERGE: Update found records in target model from id %s to id %s"
                            "" % (rec_to_remove.id, rec_to_keep.id))
                target_model_records_to_update.write({irmf_field.name: rec_to_keep.id})

    @api.model
    def _fso_merge_validate(self, rec_to_remove=None, rec_to_keep=None):
        assert rec_to_remove.ensure_one(), "Record-to-remove was not found!"
        assert rec_to_keep.ensure_one(), "Record-to-keep was not found!"

        # TODO: Move this in personemail
        # assert pe_remove.email.strip().lower() == pe_keep.email.strip().lower(), \
        #     "E-Mails must match of PersonEmail to keep (%s, %s) and PersonEmail to remove (%s, %s)!" \
        #     "" % (pe_keep.email, pe_keep.id, pe_remove.email, pe_remove.id)

    @api.model
    def _fso_merge_pre(self, rec_to_remove=None, rec_to_keep=None):
        logger.info("FSO MERGE: _fso_merge_pre()")
        return

    @api.model
    def _fso_merge_post(self, rec_to_remove=None, rec_to_keep=None):
        logger.info("FSO MERGE: _fso_merge_post()")
        return

    @api.model
    def _fso_merge_message_post(self, rec_to_remove=None, rec_to_keep=None):
        logger.info("FSO MERGE: Add merge-info-message to the chatter for record-to-keep (ID %s)" % rec_to_keep.id)
        rec_to_keep.message_post(body="FSO MERGE: Record %s (ID %s) was merged into this record!"
                                      "" % (rec_to_remove.display_name, rec_to_remove.id))

    @api.model
    def _fso_merge_unlink(self, rec_to_remove=None):
        logger.info("FSO MERGE: Unklink record-to-delete with id '%s' after merge!" % rec_to_remove.id)
        return rec_to_remove.unlink()

    @api.model
    def _fso_merge_empty_write(self, rec_to_keep=None):
        logger.info("FSO MERGE: Empty write to record-to-keep with id '%s' after merge!" % rec_to_keep.id)
        return rec_to_keep.write({})

    @api.model
    def fso_merge(self, remove_id=None, keep_id=None):
        logger.info('FSO MERGE: Started merge for model %s with record-to-keep id %s and record-to-merge id %s'
                    '' % (self._name, keep_id, remove_id))
        assert remove_id != keep_id, 'remove_id %s and keep_id %s must be different!' % (remove_id, keep_id)

        # Model information
        model_name = self._name
        model_table = self._table
        assert model_name != 'fso.merge', "Can not merge records for the abstract model 'fso.merge'!"

        # Get the records to merge
        rec_to_remove = self.browse([remove_id])
        rec_to_keep = self.browse([keep_id])

        # Validate the records to merge
        self._fso_merge_validate(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Do stuff prior to the merge
        self._fso_merge_pre(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Merge the records
        self._fso_merge_update_foreign_keys(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)
        self._fso_merge_update_reference_fields(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Do stuff after the merge
        self._fso_merge_post(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Post a chatter message for all models inheriting from the chatter
        message_post = getattr(rec_to_keep, "message_post", None)
        if callable(message_post):
            self._fso_merge_message_post(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Unlink the merged record
        self._fso_merge_unlink(rec_to_remove=rec_to_remove)

        # Start an empty write to the record to force updates if any
        self._fso_merge_empty_write(rec_to_keep=rec_to_keep)

        logger.info("FSO MERGE: Done!")
