# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields, SUPERUSER_ID
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class FSOConnectorSale(models.Model):
    """
    Connector for sale.order creation

    Additional Field Attributes:
    con = 'connector field group' If set it means that this field can be set by the JSON controller
    conupdate = connector update allowed (changes to field is allowed even if state is not 'new')
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
    # TODO: Linking
    # partner_id = fields.Many2one(comodel_name='res.partner', inverse_name="fson_con_sale_ids", readonly=True)
    # sale_order_id = fields.Many2one(comodel_name='sale.order', inverse_name="fson_con_sale_ids", readonly=True)
    # sale_order_line_id = fields.Many2one(comodel_name='sale.order.line', inverse_name="fson_con_sale_ids",
    #                                      readonly=True)
    # payment_transaction_id = fields.Many2one(comodel_name='payment.transaction', inverse_name="fson_con_sale_ids",
    #                                          readonly=True)
    # bank_id = fields.Many2one(comodel_name='res.partner.bank', inverse_name="fson_con_sale_ids",
    #                           readonly=True, help="Bankkonto (Only for payment provider FRST)")

    # ORDER: SALE ORDER
    # -----------------
    ext_order_id = fields.Char(string="Order ID", required=True, con='order',
                               help="Unique identifier from the merchant for this sale order")
    followup_for_ext_order_id = fields.Char(string="Follow Up for Order with ID", con='order', 
                                            help="Order ID of the first order that this follow up sale order is for")
    currency = fields.Selection(string='Currency', required=True, con='order', selection=[('EUR', 'EUR')])

    # ORDERLINE: SALE ORDER LINE
    # --------------------------
    #product = fields.Selection()  # Produkt (by id or xml_ref?)
    price_donate = fields.Float()  # Spende pro Stueck
    price_unit = fields.Float()    # Stueckzahl
    # payment_interval_id = fields.Many2one()  # Zahlungsintervall
    # zgruppedetail_ids = fields.Many2many()  # ZGruppeDetail

    # PARTNER: PERSON OR COMPANY (SALE ORDER / INVOICE)
    # ----------------------------------------
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
    # TODO Birthdate
    # TODO Newsletter
    is_company = fields.Boolean(string="Is a Company", con='partner', help="Ist eine Firma?")

    # EMPLOYEE: (OPTIONAL)
    # --------------------
    # HINT: Only allowed if is_company=True in the Invoice-Address above
    s_firstname = fields.Char(string="Firstname", con='employee', help="Vorname")
    s_lastname = fields.Char(string="Lastname", con='employee', required=True, help="Nachname")
    s_name_zwei = fields.Char(string="Name Zwei", con='employee', help="Name Zwei")
    s_phone = fields.Char(string="Phone", con='employee', help="Festnetznummer")
    s_mobile = fields.Char(string="Mobile Phone", con='employee', help="Mobilnummer")
    s_fax = fields.Char(string="Fax", con='employee', help="Fax")
    s_email = fields.Char(string="eMail", con='employee', help="E-Mail")
    s_street = fields.Char(string="Street", con='employee', help="Strasse")
    s_street_number_web = fields.Char(string="Street Number", con='employee', help="Hausnummer")
    s_city = fields.Char(string="City", con='employee', help="Ort")
    s_zip = fields.Char(string="ZIP", con='employee', help="Postleitzahl")
    s_country_code = fields.Char(string="Country Code", con='employee', help="Laendercode (z.B.: AT)")
    # TODO Birthdate
    # TODO Newsletter
    s_send_to_this_address = fields.Boolean(string="Send Documents to this Address", con='employee')

    # PAYMENT: PAYMENT TRANSACTION
    # ----------------------------
    # TODO: Create a new Payment provider 'fso_payment_con_sale' for fso_con_sale
    #payment_acquirer = fields.Char()                        # Payment Provider (by id or xml_ref?)
    #provider = fields.Char()                                # Zahlungsart (z.b.: VISA)

    # INFO: ADDITIONAL INFORMATION
    # ----------------------------
    origin = fields.Char(string="Origin", con='info', help="Herkunft/Quelle")

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
    def validate_records(self):
        for r in self:

            # Validate 'is_company'
            if r.is_company:
                if r.firstname:
                    raise ValidationError("Field 'firstname' is not allowed if is_company is set!")
            else:
                employee_fields = self.get_fields_by_con_group('employee')
                if any(r[fname] for fname in employee_fields):
                    raise ValidationError("Employee fields are only allowed if is_company is set!"
                                          "These fields must be empty: %s" % employee_fields)

    # ------------
    # CRUD METHODS
    # ------------
    @api.model
    def create(self, vals):
        # Create Record
        res = super(FSOConnectorSale, self).create(vals=vals)

        # Validate Records
        res.validate_records()

        # TODO: Process Record (maybe async by connector queue like screenshots)

        return res

    @api.multi
    def write(self, vals):
        res = super(FSOConnectorSale, self).write(vals=vals)

        # Validate Records
        self.validate_records()

        # TODO: Process Records (maybe async by connector queue like screenshots)

        return res
