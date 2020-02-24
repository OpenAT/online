# -*- coding: utf-8 -*-
import re


def clean_name(name, split=False, full_cleanup=True):
    # https://github.com/OpenAT/online/issues/64
    # HINT: Char fields are always unicode in odoo which is good therefore do not convert any Char fields with str()!
    # ATTENTION: Flags like re.UNICODE do NOT work all the time! Use (?u) instead in the start of any regex pattern!

    if full_cleanup:
        # Replace u., und, & with +
        name = re.sub(ur"(?u)[&]+", "+", name)
        name = re.sub(ur"(?iu)\b(und|u)\b", "+", name)
        # Remove right part starting with first +
        name = name.split('+')[0]
        # Remove unwanted words case insensitive (?i)
        # HINT: This may leave spaces or dots after the words but these get cleaned later on anyway
        name = re.sub(ur"(?iu)\b(fam|familie|sen|jun|persönlich|privat|c[/]o|anonym|e[.]u|dr|dipl|ing|mag|fh|jr)\b", "", name)

    # Remove Numbers
    name = ''.join(re.findall(ur"(?u)[^0-9]+", name))
    # Keep only unicode alphanumeric-characters (keeps chars like e.g.: Öö ỳ Ṧ), dash and space
    # HINT: This removes the left over dots from e.g.: Sen. or e.u
    name = ''.join(re.findall(ur"(?u)[\w\- ]+", name))
    # Remove leading and trailing: whitespace and non alphanumeric characters
    name = re.sub(ur"(?u)^[\W]*|[\W]*$", "", name)

    if full_cleanup:
        # Replace multiple dashes with one dash
        name = re.sub(ur"(?u)-[\s\-]*-+", "-", name)
        # Remove whitespace around dashes
        name = re.sub(ur"(?u)\s*-\s*", "-", name)
        # Replace multiple spaces with one space
        name = re.sub(ur"(?u)\s\s+", " ", name)

    # Use only first word of name
    if split:
        # Search from start until first non unicode alphanumeric-character which is not a - is reached
        # HINT: Can only be space or dash at this point ;)
        name = ''.join(re.findall(ur"(?u)^[\w\-]+", name))

    return name
