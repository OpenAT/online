# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api
import re
import phonenumbers
from psycopg2.extensions import AsIs

import logging
logger = logging.getLogger(__name__)


class ResPartnerFRSTSecurity(models.Model):
    _inherit = "res.partner"

    def init(self, cr):
        # Create a function to remove 000* at start, keep only digits, reverse the number and keep only the last 6 chars
        logger.info("Create or replace postgresql function phone_clean_reverse_6()")
        cr.execute("CREATE OR REPLACE FUNCTION phone_clean_reverse_6(text) RETURNS text AS $$"
                   "SELECT concat(left("
                   "    reverse(regexp_replace(regexp_replace($1, '[^0-9]', '', 'g'), '^000*', '')), "
                   "6));"
                   "$$ LANGUAGE 'sql' IMMUTABLE STRICT;")

        # Create the functional indexes for the phone an mobile field
        indexes = {'idx_phone_reverse': 'phone',
                   'idx_mobile_reverse': 'mobile'}
        for idx_name, idx_field in indexes.iteritems():
            logger.info("Create or replace index %s" % idx_name)
            cr.execute("""DROP INDEX IF EXISTS %s;""", (AsIs(idx_name),))
            cr.execute("""CREATE INDEX %s ON res_partner(phone_clean_reverse_6(%s));""",
                       (AsIs(idx_name), AsIs(idx_field)))

    @api.model
    def clean_phone_number(self, phone_number=str()):
        clean_whitespace_start_end = phone_number.strip()
        one_plus_at_start_and_digits_only = re.sub(r"(?!^\+)[^0-9]", "", clean_whitespace_start_end)
        two_or_more_zeros_at_start_to_plus = re.sub(r"^000*", "+", one_plus_at_start_and_digits_only)
        return two_or_more_zeros_at_start_to_plus

    @api.model
    def phone_numbers_match(self, phone_numbers, raise_parser_exception=False):
        # Clean up all given phone number strings
        phone_numbers_clean = tuple(self.clean_phone_number(pn) for pn in phone_numbers)

        # Test if the cleaned phone numbers match directly
        if all(pn == phone_numbers_clean[0] for pn in phone_numbers_clean):
            return True

        # Try to parse all numbers by the phone numbers lib
        try:
            phone_numbers_parsed = tuple(phonenumbers.parse(pn_clean) for pn_clean in phone_numbers_clean)
        except Exception as e:
            # Raise the parser exception
            if raise_parser_exception:
                raise e
            # Return False (Unequal) because we can not parse the numbers
            else:
                logger.warning("Could not parse phone numbers %s, because %s. Assuming them as unequal!"
                               "" % (phone_numbers, repr(e)))
                return False

        # Check if the parsed numbers are equal and return the boolean result
        return all(pn_parsed == phone_numbers_parsed[0] for pn_parsed in phone_numbers_parsed)

    @api.model
    def search_phone_fuzzy(self, search_phone_number):
        phone_clean = self.clean_phone_number(search_phone_number)
        assert len(phone_clean) >= 6+2, "The phone_number must be at least 8 digits long! (%s)" % search_phone_number
        cr = self.env.cr

        # Fuzzy search for records where the last six digits of given number match in the database
        found = dict()
        for phone_field in ('phone', 'mobile'):
            # 'fuzzy' sql search for partners with this number
            cr.execute("""SELECT id, %(phone_field)s FROM res_partner 
                          WHERE phone_clean_reverse_6(%(phone_field)s) = phone_clean_reverse_6(%(phone_number)s);
                       """,
                       {'phone_field': AsIs(phone_field),
                        'phone_number': search_phone_number}
                       )
            search_res = cr.dictfetchall()

            # Filter out non exact matches (Compare the found results with the phone_numbers_match() method)
            for record in search_res:
                record_id, record_phone_number = record['id'], record[phone_field]
                if self.phone_numbers_match((record_phone_number, search_phone_number)):
                    if record_id not in found:
                        found[record_id] = {'search_phone_number': search_phone_number,
                                            phone_field: record_phone_number}
                    else:
                        found[record_id][phone_field] = record_phone_number

        return found
