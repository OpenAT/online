# -*- coding: utf-8 -*-
import re
# HINT: https://regex101.com/

# -----------------------------------------------------------
# Contains helper methods for address cleanup and recognition
# -----------------------------------------------------------


def clean_street(street, remove_building_number=True):
    # HINT: Char fields are always unicode in odoo which is good therefore do not convert any Char fields with str()!
    # ATTENTION: Flags like re.UNICODE do NOT work all the time! Use (?u) instead in the start of any regex pattern!

    # Replace multiple spaces with one space
    street = re.sub(ur"(?u)\s\s+", " ", street)

    if remove_building_number:
        # Only keep words starting with three or more non numerical characters
        # (\b = word boundary, \D = Non digit chars)
        street = ''.join(re.findall(ur"(?u)\b\D{3,}", street))

    # Remove leading and trailing: whitespace and non alphanumeric characters
    street = re.sub(ur"(?u)^[\W]*|[\W]*$", "", street)

    return street
