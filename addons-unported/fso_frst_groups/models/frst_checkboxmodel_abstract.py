# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTCheckboxModel(models.AbstractModel):
    """
    USAGE:
        checkbox model:
            must inherit 'frst.checkboxmodel'
            '_bridge_model_fields' must be set

        bridge model:
            must inherit 'frst.gruppestate' FIRST and then 'frst.checkboxbridgemodel'
           _group_model_field, _checkbox_model_field and _checkbox_fields_group_identifier must be set

    ATTENTION: A Checkbox is 'Set/True' if there are subscribed bridge model records AND NO unsubscribed bm records!
    """
    _name = "frst.checkboxmodel"

    # List of all One2many fields pointing to bridge models
    # HINT: MUST BE DEFINED IN THE CHECKBOX MODEL!
    _bridge_model_fields = tuple()

    # --------------
    # CHECKBOX MODEL
    # --------------
    # Compute combined bridge models configurations
    @api.model
    def get_bridge_models_config(self):
        logger.debug("Compute '_bridge_models_config' for checkbox model %s" % self.__class__.__name__)
        config = {}

        # Loop through bridge model fields
        for field in self._bridge_model_fields:
            bridge_model_field_obj = self._fields.get(field)
            bridge_model_name = bridge_model_field_obj.comodel_name

            # Get the config from the bridge model
            bridge_model_config = self.env[bridge_model_name].sudo().get_checkboxgroup_config()

            # Update '_bridge_models_config' with the config from the bridge model
            config[bridge_model_name] = {
                'bridge_model_field': bridge_model_field_obj.name,
                'bridge_model_config': bridge_model_config,
            }

        return config

    # Action at checkbox set:
    @api.multi
    def set_bm_group(self, group_id=None, bm_field='', bm_group_model_field='', bm_checkbox_model_field='',
                     checkbox_field=''):
        """
        This method is called when a checkbox that is linked to a group (zGruppeDetail) is set.

        HINT: It is possible in FRST that the same group is assigned (by the bridge model) multiple times.
              Therefore the handling what to enable or disable is way more complicated!
        """
        group_id = int(group_id)

        # Loop through checkbox model records
        for r in self:

            # Get all bridge model records for this group (for the current checkbox model record)
            group_bm_records = r[bm_field].filtered(lambda bm: bm[bm_group_model_field].id == group_id)

            # Checkbox 'not set' states:
            unsubscribed = group_bm_records.filtered(lambda g: g.state == 'unsubscribed')
            expired = group_bm_records.filtered(lambda g: g.state == 'expired')

            # Checkbox 'set' states:
            subscribed = group_bm_records.filtered(lambda g: g.state == 'subscribed')
            approval_pending = group_bm_records.filtered(lambda g: g.state == 'approval_pending')
            approved = group_bm_records.filtered(lambda g: g.state == 'approved')

            # Get bestaetigung_erforderlich field value from the group (zGruppeDetail)
            # Get _approval_pending_date from Bridge Model (e.g. PersonEmailGruppe)
            bridge_model_name = self._fields.get(bm_field).comodel_name
            bridge_model_object = self.env[bridge_model_name].sudo()

            group_model_name = bridge_model_object._fields.get(bm_group_model_field).comodel_name
            group = self.env[group_model_name].sudo().search([('id', '=', group_id)])

            approval_needed = group.bestaetigung_erforderlich
            approval_pending_date = bridge_model_object._approval_pending_date

            # A) No Bridge Model Group Record exists at all:
            # ----------------------------------------------
            if not group_bm_records:
                # Split . notation in bm_checkbox_model_field
                # e.g.: 'frst_personemail_id.partner_id'.rsplit('.')[0] = 'frst_personemail_id'
                bm_target_model_field = bm_checkbox_model_field.rsplit('.')[0]

                # Get bm_target_model_field_id
                bridge_model_name = self._fields.get(bm_field).comodel_name
                bmo = self.env[bridge_model_name].sudo()
                bm_target_model_field_id = bmo.get_target_model_id_from_checkbox_record(checkbox_record=r)

                # Check if a target model record exist already and continue if not
                # HINT: We could also unset the checkbox_field here but it seems better to just leave it alone
                #       Example: Someone enabled 'newsletter_web' with no email (= no 'main_personemail_id')
                #                This seems ok because if someone was logged in he/she would see that
                #                "newsletter_web" is already set und can 'mindfully' unset it. If not logged in
                #                merge contacts should leave "newsletter_web" alone.
                if not bm_target_model_field_id:
                    logger.warning("Could not get target_model_id for bridge model %s for checkbox field %s! (Checkbox "
                                   "model: %s, record ID: %s)." % (bridge_model_name, checkbox_field,
                                                                   self.__class__.__name__, r.id))
                    continue

                # Compute gueltig_von and gueltig_bis based on approval_needed
                gueltig_von = fields.datetime.now() if not approval_needed else approval_pending_date
                gueltig_bis = fields.date(2099, 12, 31) if not approval_needed else approval_pending_date

                # Create the bridge model record
                vals = {bm_target_model_field: bm_target_model_field_id,
                        bm_group_model_field: group_id,
                        'steuerung_bit': True,
                        'gueltig_von': gueltig_von,
                        'gueltig_bis': gueltig_bis,
                        }
                group_bm_records.sudo().with_context(skipp_group_to_checkbox=True).create(vals)
                continue

            # B) Bridge Model Group Records exists already for "Checkbox Set"
            # ---------------------------------------------------------------
            if subscribed or approval_pending or approved:
                # Expire unsubscribed bridge model records!
                if unsubscribed:
                    unsubscribed.sudo().with_context(skipp_group_to_checkbox=True).write(
                        {'gueltig_bis': fields.datetime.now() - timedelta(days=1)})
                continue

            # C) No Bridge Model Group Records for "Checkbox Set" but for "Checkbox not Set" exists
            # -------------------------------------------------------------------------------------
            if unsubscribed:
                # Enable newest unsubscribed bridge model record
                # HINT: gueltig_von and gueltig_bis must be ok/'active' or the group would be in state 'expired'!
                #       Therefore we do not need to check or set these fields
                unsub_rec = unsubscribed.sorted(key=lambda k: k.write_date, reverse=True)[0]
                unsub_rec.sudo().with_context(skipp_group_to_checkbox=True).write({'steuerung_bit': False})
                continue
            elif expired:
                # Enable newest expired bridge model record
                expired_rec = expired.sorted(key=lambda k: k.write_date, reverse=True)[0]

                # Compute gueltig_von and gueltig_bis based on approval_needed and the current value
                # HINT: Only change gueltig_von and gueltig_bis if needed!
                gueltig_von = fields.datetime.strptime(expired_rec.gueltig_von, DEFAULT_SERVER_DATE_FORMAT)
                gueltig_bis = fields.datetime.strptime(expired_rec.gueltig_bis, DEFAULT_SERVER_DATE_FORMAT)
                if approval_needed:
                    gueltig_von = approval_pending_date
                    gueltig_bis = approval_pending_date
                else:
                    if gueltig_von > fields.datetime.now():
                        gueltig_von = fields.datetime.now()
                    if gueltig_bis < fields.datetime.now():
                        gueltig_bis = fields.date(2099, 12, 31)

                # Enable newest expired bridge model record
                expired_rec.sudo().with_context(skipp_group_to_checkbox=True).write(
                    {'gueltig_von': gueltig_von, 'gueltig_bis': gueltig_bis, })
                continue

            # D) If we come here something is really went wrong!
            raise AssertionError("set_bm_group() Error for checkbox field %s, checkbox model: %s and record ID: %s)."
                                 "" % (checkbox_field, self.__class__.__name__, r.id))

        return True

    # Action at checkbox unset:
    @api.multi
    def rem_bm_group(self, group_id=None, bm_field='', bm_group_model_field=''):
        group_id = int(group_id)

        # Loop through checkbox model records
        for r in self:
            # Get all bridge model records for this group for the current checkbox model record
            group_bm_records = r[bm_field].filtered(
                lambda bm: bm[bm_group_model_field].id == group_id)

            # Get bridge model records by bridge model state
            checkbox_set = group_bm_records.filtered(
                lambda g: g.state in ('subscribed', 'approved', 'approval_pending'))

            # HINT: Right now we agreed to expire the bm_groups but it might be also "legit" if we "unsubscribe" the
            #       group if someone unsets the checkbox.
            # HINT: Since we set 'gueltig_von' and 'gueltig_bis' to something else than the _approval_pending_date
            #       It will also work as expected for 'approval_pending' bridge model records.
            #       There is a special handling in set_bm_group() if we re-enable a bm_group where the
            #       option 'approval_needed' is honoured again for gueltig_bis and gueltig_von!
            if checkbox_set:
                # Expire all subscribed bridge model records where the checkbox is currently set
                # TODO: Discuss if we should set gueltig_von also ?!?
                checkbox_set.sudo().with_context(skipp_group_to_checkbox=True).write(
                    {'gueltig_bis': fields.datetime.now() - timedelta(days=1)})

        return True

    @api.multi
    def checkbox_to_group(self, values=None):
        """ This method will create/subscribe or expire/unsubscribe all groups based on the checkbox fields.
            It can be used to restore all groups based on the checkbox values
            It is fired by the CRUD methods of the checkbox model
            If 'values' is not given it will update the groups for all checkbox fields
        """
        context = self.env.context or {}
        values = values or {}

        # Recursion switch
        if 'skipp_checkbox_to_group' in context:
            return True

        bridge_models_config = self.get_bridge_models_config()

        # Loop through bridge models
        for bridge_model, config in bridge_models_config.iteritems():
            bm_field = config['bridge_model_field']
            bm_config = config['bridge_model_config']
            bm_group_model_field = bm_config['group_model_field']
            bm_checkbox_model_field = bm_config['checkbox_model_field']

            # Process all checkbox fields if called without values
            if values is None:
                checkbox_fields = {f: g for f, g in bm_config['fields_to_groups'].iteritems()}

            # Process only checkbox fields in values
            else:
                values = values or {}
                checkbox_fields = {f: g for f, g in bm_config['fields_to_groups'].iteritems() if f in values}

            # Continue to next bridge model if no fields are configured or in values
            if not checkbox_fields:
                continue

            # Loop through the checkbox model
            for r in self:

                # Loop through the checkbox fields
                for cf_name, group in checkbox_fields.iteritems():

                    # Safety switch e.g. after main email creation where group_to_checkbox() would unset checkboxes
                    if values:
                        if r[cf_name] != values[cf_name]:
                            r.write({cf_name: values[cf_name]})

                    # Checkbox is True/Set
                    if r[cf_name]:
                        r.set_bm_group(group_id=group.id,
                                       bm_field=bm_field,
                                       bm_group_model_field=bm_group_model_field,
                                       bm_checkbox_model_field=bm_checkbox_model_field,
                                       checkbox_field=cf_name)
                    # Checkbox is False/Unset
                    else:
                        r.rem_bm_group(group_id=group.id,
                                       bm_field=bm_field,
                                       bm_group_model_field=bm_group_model_field)

        return True

    @api.multi
    def group_to_checkbox(self, values=None):
        """ This method will set or unset all checkboxes based on the current groups.
            It can be used to restore all checkbox values based on the groups
            It is fired by the CRUD methods of the bridge model
        """
        context = self.env.context or {}

        # Recursion switch to be used in inverse method 'checkbox_to_group'
        if 'skipp_group_to_checkbox' in context:
            return

        bridge_models_config = self.get_bridge_models_config()

        # Loop through checkbox model records
        for r in self:

            # Loop through bridge models
            for bridge_model_name, config in bridge_models_config.iteritems():
                bm_field = config['bridge_model_field']
                bm_config = config['bridge_model_config']
                bm_group_model_field = bm_config['group_model_field']
                bm_checkbox_model_field = bm_config['checkbox_model_field']

                # Loop through all groups mapped to a checkbox
                for checkbox_field_name, group in bm_config['fields_to_groups'].iteritems():
                    
                    # Get all bridge model records for this group for the current checkbox model record
                    # ---
                    checkbox_record_bm_records = r[bm_field]
                    group_bm_records = checkbox_record_bm_records.filtered(
                        lambda bm: bm[bm_group_model_field].id == group.id)

                    # Get all approval_pending bridge model records for this group for the current checkbox model record
                    approval_pending = group_bm_records.filtered(lambda bm: bm.state == 'approval_pending')

                    # Get all subscribed bridge model records for this group for the current checkbox model record
                    subscribed = group_bm_records.filtered(lambda bm: bm.state == 'subscribed')

                    # Get all approved bridge model records for this group for the current checkbox model record
                    approved = group_bm_records.filtered(lambda bm: bm.state == 'approved')

                    # Get all unsubscribed bridge model records for this group for the current checkbox model record
                    unsubscribed = group_bm_records.filtered(lambda bm: bm.state == 'unsubscribed')

                    # Check a group is not subscribed and unsubscribed through a bridge model record at the same time
                    # HINT: The same group (zGruppeDetail) could theoretically be assigned multiple times!
                    #       e.g. via personemailgruppe.
                    if (subscribed or approved or approval_pending) and unsubscribed:
                        logger.error("Group is (subscribed or approved or approval_pending) and unsubscribed at the "
                                     "same time! bridge_model: %s, checkbox_model %s ID %s, group_id %s"
                                     "" % (bridge_model_name, r._name, r.id, group.id))
                    
                    # Compute the checkbox field value
                    value = True if (subscribed or approved or approval_pending) and not unsubscribed else False

                    # Update the checkbox field value if needed
                    if value != r[checkbox_field_name]:
                        r.sudo().with_context(skipp_checkbox_to_group=True).write({checkbox_field_name: value})

        return True

    # ----
    # CRUD
    # ----

    # ----------------------------------------------------------------------------------------------------------------
    # ATTENTION: !!! Methods in Abstract model may ignore the inheritance order created by addon dependency !!!
    #            Therefore we need to create the crud methods directly in the checkbox model and disable them here! :(
    #            !!! This is an odoo framework bug of odoo 8 and should not exists in odoo 12 anymore !!!
    # ----------------------------------------------------------------------------------------------------------------

    # @api.model
    # def create(self, values):
    #     values = values or {}
    #     context = self.env.context or {}
    #
    #     res = super(FRSTCheckboxModel, self).create(values)
    #
    #     # Checkboxes to groups
    #     if 'skipp_checkbox_to_group' not in context:
    #         res.checkbox_to_group(values)
    #
    #     return res
    #
    # @api.multi
    # def write(self, values):
    #     values = values or {}
    #     context = self.env.context or {}
    #
    #     res = super(FRSTCheckboxModel, self).write(values)
    #
    #     # Checkboxes to groups
    #     if 'skipp_checkbox_to_group' not in context:
    #         self.checkbox_to_group(values)
    #
    #     return res
