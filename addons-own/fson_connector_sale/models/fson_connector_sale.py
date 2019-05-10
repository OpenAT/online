# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields, SUPERUSER_ID
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class FSOConnectorSale(models.Model):
    """
    Connector for sale.order creation

    Additional Field Attributes:
    con = 'connector field group'   If set it means that this field can be set by the JSON controller
    con_update = True/False         If True an Update to the field is allowed
    """
    _name = "fson.connector.sale"

    # HINT: Check get_fields_by_con_group()
    # ATTENTION: key 'all_con_fields' holds a list with all fields!
    _fields_by_con_group = dict()

    # --------------------------
    # FIELDS
    # --------------------------

    # INTERNAL FIELDS
    # ----------------
    # Status and logs
    state = fields.Selection(selection=[('new', 'New'),
                                        ('update', 'Update'),
                                        ('done', 'Done'),
                                        ('error', 'Error')],
                             string="State", readonly=True)
    received_data_log = fields.Text(string="Received-Data Log",
                                    readonly=True)
    received_data_date = fields.Datetime(string="Received Data at", readonly=True)
    error_details = fields.Text(string='Error Details', readonly=True)

    # Linking
    partner_id = fields.Many2one(comodel_name='res.partner', inverse_name="fson_connector_sale_ids",
                                 readonly=True, index=True)
    employee_id = fields.Many2one(comodel_name='res.partner', inverse_name="fson_connector_sale_employee_ids",
                                  readonly=True, index=True)
    donee_id = fields.Many2one(comodel_name='res.partner', inverse_name="fson_connector_sale_donee_ids",
                               readonly=True, index=True)
    sale_order_id = fields.Many2one(comodel_name='sale.order', inverse_name="fson_connector_sale_ids",
                                    readonly=True, index=True)
    sale_order_line_id = fields.Many2one(comodel_name='sale.order.line', inverse_name="fson_connector_sale_ids",
                                         readonly=True, index=True)
    payment_transaction_id = fields.Many2one(comodel_name='payment.transaction', inverse_name="fson_connector_sale_ids",
                                             readonly=True, index=True)

    # ORDER: SALE ORDER
    # -----------------
    ext_order_id = fields.Char(string="Order ID", required=True, con='order',
                               help="Unique identifier from the merchant for this sale order")
    followup_for_ext_order_id = fields.Char(string="Follow Up for Order with ID", con='order', 
                                            help="Order ID of the first order that this followup-sale-order is for")
    currency = fields.Selection(string='Currency', required=True, con='order', selection=[('EUR', 'EUR')])

    # ORDERLINE: SALE ORDER LINE
    # --------------------------
    product = fields.Char(string="Product", required=True, con='orderline',
                          help="ID (INTEGER) of the Product")
    price_donate = fields.Float()                         # Spende pro Stueck
    price_unit = fields.Float()                           # Stueckzahl
    amount_total = fields.Float()                         # Sale Order Amount Total (must be price_donate * price_unit)
    payment_interval_id = fields.Char()                   # Zahlungsintervall
    zgruppedetail_ids = fields.Char()                     # ZGruppeDetail IDS

    # ADDITIONAL INFORMATION
    # ----------------------
    origin = fields.Char(string="Origin", con='info', help="Herkunft/Quelle e.g.: Website, URL or Campaign Name")
    notes = fields.Char(string="Notes", con='info', help="Additional Information")

    # PARTNER: PERSON OR COMPANY (TO INVOICE)
    # ---------------------------------------
    # Contract-Participant: Private-Person or Legal-Company to Invoice
    # ATTENTION: The contract will be concluded with this Person or Company!
    firstname = fields.Char(string="Firstname", con='partner', help="Vorname (Can not be set if this is a company!)")
    lastname = fields.Char(string="Lastname", con='partner', required=True, help="Nachname")
    name_zwei = fields.Char(string="Name Zwei", con='partner', help="Name Zwei")
    phone = fields.Char(string="Phone", con='partner', help="Festnetznummer")
    mobile = fields.Char(string="Mobile Phone", con='partner', help="Mobilnummer")
    fax = fields.Char(string="Fax", con='partner', help="Fax")
    email = fields.Char(string="eMail", con='partner', help="E-Mail")
    street = fields.Char(string="Street", con='partner', help="Strasse")
    street_number_web = fields.Char(string="Street Number", con='partner', help="Hausnummer")
    city = fields.Char(string="City", con='partner', help="Ort")
    zip = fields.Char(string="ZIP", con='partner', help="Postleitzahl")
    country_code = fields.Char(string="Country Code", con='partner', help="Laendercode (z.B.: AT)")
    birthdate_web = fields.Date(string="Birthdate", con='partner', help="Geburtsdatum")
    newsletter_web = fields.Boolean(string="Newsletter", con='partner', help="Newsletter")
    is_company = fields.Boolean(string="Is a Company", con='partner', help="Ist eine Firma?")

    # EMPLOYEE: (OPTIONAL) (Mitarbeiter)
    # ----------------------------------
    # ATTENTION: Only allowed if is_company=True in the Invoice-Address above
    e_firstname = fields.Char(string="Firstname", con='employee', help="Vorname")
    e_lastname = fields.Char(string="Lastname", con='employee', required=True, help="Nachname")
    e_name_zwei = fields.Char(string="Name Zwei", con='employee', help="Name Zwei")
    e_phone = fields.Char(string="Phone", con='employee', help="Festnetznummer")
    e_mobile = fields.Char(string="Mobile Phone", con='employee', help="Mobilnummer")
    e_fax = fields.Char(string="Fax", con='employee', help="Fax")
    e_email = fields.Char(string="eMail", con='employee', help="E-Mail")
    e_street = fields.Char(string="Street", con='employee', help="Strasse")
    e_street_number_web = fields.Char(string="Street Number", con='employee', help="Hausnummer")
    e_city = fields.Char(string="City", con='employee', help="Ort")
    e_zip = fields.Char(string="ZIP", con='employee', help="Postleitzahl")
    e_country_code = fields.Char(string="Country Code", con='employee', help="Laendercode (z.B.: AT)")
    e_birthdate_web = fields.Date(string="Birthdate", con='employee', help="Geburtsdatum")
    e_newsletter_web = fields.Boolean(string="Newsletter", con='employee', help="Newsletter")
    e_send_to_this_address = fields.Boolean(string="Send Documents to this Address", con='employee')

    # DONEE: (OPTIONAL) (Beschenkter/Zuwendungsaempfenger)
    # ----------------------------------------------------
    d_firstname = fields.Char(string="Firstname", con='donee', help="Vorname")
    d_lastname = fields.Char(string="Lastname", con='donee', required=True, help="Nachname")
    d_name_zwei = fields.Char(string="Name Zwei", con='donee', help="Name Zwei")
    d_phone = fields.Char(string="Phone", con='donee', help="Festnetznummer")
    d_mobile = fields.Char(string="Mobile Phone", con='donee', help="Mobilnummer")
    d_fax = fields.Char(string="Fax", con='donee', help="Fax")
    d_email = fields.Char(string="eMail", con='donee', help="E-Mail")
    d_street = fields.Char(string="Street", con='donee', help="Strasse")
    d_street_number_web = fields.Char(string="Street Number", con='donee', help="Hausnummer")
    d_city = fields.Char(string="City", con='donee', help="Ort")
    d_zip = fields.Char(string="ZIP", con='donee', help="Postleitzahl")
    d_country_code = fields.Char(string="Country Code", con='donee', help="Laendercode (z.B.: AT)")
    d_birthdate_web = fields.Date(string="Birthdate", con='donee', help="Geburtsdatum")
    d_newsletter_web = fields.Boolean(string="Newsletter", con='donee', help="Newsletter")
    d_send_to_this_address = fields.Boolean(string="Send Documents to this Address", con='donee')

    # PAYMENT: PAYMENT TRANSACTION
    # ----------------------------

    # Base Fields
    # -----------
    acquirer_id = fields.Many2one(string="Acquirer", required=True)
    acquirer_reference = fields.Char(string="Acquirer Transaction Reference")
    date_validate = fields.Datetime(string="Validation Date")
    # reference = fields.Char(string="Order Reference")
    #             # ext_order_id OR request.env['payment.transaction'].get_next_reference(order.name)
    # amount = fields.Float() not needed since we have price donate     # = sale_order_id.amount_total
    # currency_id = fields.Many2one()                                   # = currency
    # fees = fields.Float()
    # type = fields.Selection()                  # = 'form'
    # state = fields.Selection()                 # should be set by *_form_validate
    # partner_id = fields.Many2one()             # sale_order_id.partner_id OR partner_id
    # partner_country_id = Fields.Many2one()     # sale_order_id.partner_id.country_id.id OR partner_id.country_id.id
    # sale_order_id         # sale_order_id.id

    # Payment Method: payment_fsotransfer (Zahlschein)
    # ------------------------------------------------
    do_not_send_payment_forms = fields.Boolean(string="Do not send payment forms")

    # Payment Method: payment_frst (Bankeinzug)
    # -----------------------------------------
    frst_iban = fields.Char(string="IBAN")
    frst_bic = fields.Char(string="BIC (optional)")

    # Payment Method: TODO: payment_consale (Webschnittstelle/Extern)
    # ---------------------------------------------------------------
    consale_state = fields.Selection(string="Payment Transaction State")
    consale_payment_method = fields.Selection(string="Payment Method (PM)")
    consale_brand = fields.Char(string="Brand (BRAND)")

    # consale_trxdate = fields.Datetime(string="Transaction Date and Time (TRXDATE)")
    # consale_common_name = fields.Char("Common Name (CN)")
    # consale_eci = fields.Char(string="Electronic Commerce Indicator (ECI)")
    # consale_expiry_date = fields.Char(string="Expiry Date (ED)")
    # consale_payid = fields.Char(string="PayID")

    # --------------------------
    # CONSTRAINTS AND VALIDATION
    # --------------------------
    # https://www.postgresql.org/docs/9.3/static/ddl-constraints.html
    _sql_constraints = [
        ('ext_order_id_unique', 'UNIQUE(ext_order_id)', "'ext_order_id' must be unique!"),
    ]

    # --------------
    # HELPER METHODS
    # --------------
    @api.model
    def get_fields_by_con_group(self, con_group=''):
        # HINT: use key 'all_con_fields' to get all connector fields of all groups

        # Update class attribute if needed
        if not self._fields_by_con_group:
            cls = type(self)
            fbcg = dict()
            fbcg['all_con_fields'] = list()
            for fname, field in self._fields.iteritems():
                if hasattr(field, "_attrs") and 'con' in field._attrs:
                    # Special key holding all connector fields
                    fbcg['all_con_fields'].append(fname)
                    # Append field name to the group list
                    con_group_name = field._attrs['con']
                    if con_group_name not in fbcg:
                        fbcg[con_group_name] = list()
                    fbcg[con_group_name].append(fname)
            # Store result in class attribute
            cls._fields_by_con_group = fbcg

        # Return fields
        field_names = self._fields_by_con_group[con_group]
        assert field_names, "No Fields found for con_group %s" % con_group
        return field_names

    # ------------------
    # VALIDATION METHODS
    # ------------------
    @api.multi
    def validate_data(self):
        for r in self:
            logger.info("fson_connector_sale() validate input data")

            # Validate 'is_company'
            if r.is_company:
                if r.firstname:
                    raise ValidationError("Field 'firstname' is not allowed if 'is_company' is set!")
            elif not r.is_company:
                employee_fields = self.get_fields_by_con_group('employee')
                if any(r[fname] for fname in employee_fields):
                    raise ValidationError("Employee fields are only allowed if 'is_company' is set!"
                                          "These fields must be empty: %s" % employee_fields)

    # ------------------------------
    # CONVERSION AND LINKING METHODS
    # ------------------------------
    @api.multi
    def add_partner(self):
        assert self.ensure_one(), "Only one record allowed"
        logger.info("Create Partner/Company to invoice for %s" % self.id)

        # Create Partner
        partner = 'TODO'

        # Link Partner
        self.write({'partner_id': partner.id})

        return partner

    @api.multi
    def add_partner_employee(self):
        assert self.ensure_one(), "Only one record allowed"
        logger.info("Create Employee for %s" % self.id)

        # Create Employee
        employee = 'TODO'

        # Link Employee
        self.write({'employee_id': employee.id})

        return employee

    @api.multi
    def add_partner_donee(self):
        assert self.ensure_one(), "Only one record allowed"
        logger.info("Create Donee for %s" % self.id)

        # Create Donee
        donee = 'TODO'

        # Link Donee
        self.write({'donee_id': donee.id})

        return donee

    @api.multi
    def add_sale_order(self):
        assert self.ensure_one(), "Only one record allowed"
        logger.info("Create Sale Order for %s" % self.id)

        # Make sure partner already exists
        assert self.partner_id, "Partner is missing!"

        # Create Sale Order
        sale_order = 'TODO'

        # Link Sale Order
        self.write({'sale_order_id': sale_order.id})

        return sale_order

    @api.multi
    def add_sale_order_line(self,):
        assert self.ensure_one(), "Only one record allowed"
        logger.info("Create Sale Order Line for %s" % self.id)

        # Create Sale Order Line
        so_line = 'TODO'

        # Link Sale Order Line
        self.write({'sale_order_line_id': so_line.id})

        return so_line

    @api.multi
    def add_payment_transaction(self):
        assert self.ensure_one(), "Only one record allowed"
        logger.info("Create Payment Transaction for %s" % self.id)

        # Create Payment Transaction
        tx = 'TODO'

        # Link Payment Transaction
        self.write({'payment_transaction_id': tx.id})

        return tx

    @api.multi
    def create_order(self):
        for r in self:
            logger.info("fson_connector_sale() create order for record %s" % r.id)

            # VALIDATE DATA
            # -------------
            r.validate_data()

            # CREATE AND LINK RECORDS
            # -----------------------
            # Add Partner
            partner = r.add_partner()

            # Add Employee
            employee = r.add_partner_employee()

            # Add Donee
            donee = r.add_partner_donee()

            # Add Sale.Order
            sale_order = r.add_sale_order()

            # Add Sale.Order.Line
            so_line = r.add_sale_order_line()

            # Create and link Payment.Transaction
            tx = r.add_payment_transaction

            # Update Sale.Order State (Maybe not needed because done by payment.transaction?!? To be tested)

    @api.multi
    def update_order(self, vals=None):
        for r in self:
            logger.info("fson_connector_sale() process update for record %s" % r.id)

            # TODO: Check it the record data and the linked partner data still matches
            # TODO: Process the Update for the linked records

    # ------------
    # CRUD METHODS
    # ------------
    @api.model
    def create(self, vals):
        # Create Record
        record = super(FSOConnectorSale, self).create(vals=vals)

        # Validate Data and Process Record
        if any(f in vals for f in self.get_fields_by_con_group('all_con_fields')):
            record.create_order()

        return record

    @api.multi
    def write(self, vals):
        update_not_allowed = self.get_fields_by_con_group('no_update')
        fields_not_allowed = tuple(f for f in update_not_allowed if f in vals)
        assert not fields_not_allowed, "Update for fields %s is not allowed!" % fields_not_allowed

        # Update Records
        res = super(FSOConnectorSale, self).write(vals=vals)

        # Validate Data and Process Records
        if any(f in vals for f in self.get_fields_by_con_group('update')):
            self.update_order(vals=vals)

        return res
