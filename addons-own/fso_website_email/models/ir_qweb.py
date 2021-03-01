# -*- coding: utf-8 -*-
"""
Website-context rendering needs to add some metadata to rendered fields,
as well as render a few fields differently.

Also, adds methods to convert values back to openerp models.
"""

import logging
from bs4 import BeautifulSoup, element, NavigableString
from lxml import etree, html
import re
from copy import deepcopy

from openerp.osv import orm, fields

logger = logging.getLogger(__name__)


class Text(orm.AbstractModel):
    _name = 'website.qweb.field.text'
    _inherit = ['website.qweb.field', 'ir.qweb.field.text']

    def from_html(self, cr, uid, model, field, element, context=None):

        # Text only fields parsing is messed up in odoo 8 therefore we made our own just for the field fso_email_text
        if model and model._name == 'email.template' and field and field.name == 'fso_email_text':
            # Fix CK-Editor markup
            html_shard = html.tostring(element)
            html_fixed = fix_ck_level1(html_shard, start_tag_id='fso_email_text')

            logger.debug("Original html for fso_email_text: %s" % html_shard)
            logger.info("Fixed html for fso_email_text: %s" % html_fixed)

            fixed_element = html.fromstring(html_fixed, parser=html.HTMLParser(encoding='utf-8'))
            res = html_to_text_fso_email_text(fixed_element)

        else:
            res = super(Text, self).from_html(cr, uid, model, field, element, context=context)

        return res


BLOCK_LEVEL_TAGS = ('div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'address', 'article', 'aside', 'blockquote',
                    'canvas', 'dd', 'dl', 'figcaption', 'figure', 'form', 'hr', 'ol', 'ul', 'pre', 'section')


def fix_ck_level1(html_shard, start_tag_id=""):
    bs4_soup = BeautifulSoup(html_shard, features="html.parser")
    if start_tag_id:
        content = bs4_soup.find(id='fso_email_text')

    # Make sure all level 1 text containing elements are wrapped in a <div> tag except for br tags
    for child in content.children:

        # Wrap NavigableStrings or non block level tags in a <div> tag
        if type(child) is element.NavigableString or child.name not in BLOCK_LEVEL_TAGS:
            # Get all line elements
            line = [child,]
            for sibling in child.next_siblings:
                # Stop at the next block level element
                if sibling.name in BLOCK_LEVEL_TAGS:
                    break
                line.append(sibling)

            # Create a new div tag and append the line elements
            # HINT: This will also (re)move the line elements from the other bs4 soup parse tree
            new_div = bs4_soup.new_tag("div")
            for s in line:
                new_div.append(deepcopy(s))

            # Skipp if no text was found at all in the line elements
            text = "".join([repr(string) for string in new_div.stripped_strings])
            if not text:
                continue

            # Replace the child element with the new div tag
            child.replace_with(new_div)

            # Remove the siblings
            for sibling in line[1:]:
                sibling.extract()

    # Collapse linebreak only elements
    for child in content.children:

        if child.name == 'br':
            continue

        # Replace block level elements on level 1 containing no text but just br tags
        if child.name in BLOCK_LEVEL_TAGS:
            # Get text from all descendants omitting empty strings and removing extra white space
            text = "".join([repr(string) for string in child.stripped_strings])
            if not text:
                newlines = len([br for br in child.find_all('br')])

                # clear the contents
                #child.clear()

                # Add a non breaking space &nbsp; so there is some text in it
                #child.string = u"\xa0"

                # Add extra br tags based on newlines - 1
                if newlines > 1:
                    for line in range(newlines - 1):
                        child.insert_after(bs4_soup.new_tag('br'))

                child.replace_with(bs4_soup.new_tag('br'))
                #child.extract()

                continue

    # Normalize as much as possible
    pretty = bs4_soup.prettify()
    flat = re.sub(u'\n', u'', pretty)
    return flat


def html_to_text_fso_email_text(element):
    """ Converts HTML content with HTML-specified line breaks (br, p, div, ...)
    in roughly equivalent textual content.

    Used to replace and fixup the roundtripping of text and m2o: when using
    libxml 2.8.0 (but not 2.9.1) and parsing HTML with lxml.html.fromstring
    whitespace text nodes (text nodes composed *solely* of whitespace) are
    stripped out with no recourse, and fundamentally relying on newlines
    being in the text (e.g. inserted during user edition) is probably poor form
    anyway.

    -> this utility function collapses whitespace sequences and replaces
       nodes by roughly corresponding linebreaks
       * p are pre-and post-fixed by 2 newlines
       * br are replaced by a single newline
       * block-level elements not already mentioned are pre- and post-fixed by
         a single newline

    ought be somewhat similar (but much less high-tech) to aaronsw's html2text.
    the latter produces full-blown markdown, our text -> html converter only
    replaces newlines by <br> elements at this point so we're reverting that,
    and a few more newline-ish elements in case the user tried to add
    newlines/paragraphs into the text field

    :param element: lxml.html content
    :returns: corresponding pure-text output
    """

    # output is a list of str | int. Integers are padding requests (in minimum
    # number of newlines). When multiple padding requests, fold them into the
    # biggest one
    output = []
    _wrap(element, output)

    # remove any leading or tailing whitespace, replace sequences of
    # (whitespace)\n(whitespace) by a single newline, where (whitespace) is a
    # non-newline whitespace in this case
    return re.sub(
        r'[ \t\r\f]*\n[ \t\r\f]*',
        '\n',
        ''.join(_realize_padding(output)).strip())

_PADDED_BLOCK = set('p h1 h2 h3 h4 h5 h6'.split())

# https://developer.mozilla.org/en-US/docs/HTML/Block-level_elements minus p
_MISC_BLOCK = set((
    'address article aside audio blockquote canvas dd dl div figcaption figure'
    ' footer form header hgroup hr ol output pre section tfoot ul video'
).split())


def _collapse_whitespace(text):
    """ Collapses sequences of whitespace characters in ``text`` to a single
    space
    """
    return re.sub('\s+', ' ', text)


def _realize_padding(it):
    """ Fold and convert padding requests: integers in the output sequence are
    requests for at least n newlines of padding. Runs thereof can be collapsed
    into the largest requests and converted to newlines.
    """
    padding = None
    for item in it:
        if isinstance(item, int):
            padding = max(padding, item)
            continue

        if padding:
            yield '\n' * padding
            padding = None

        yield item
    # leftover padding irrelevant as the output will be stripped


def _wrap(element, output, wrapper=u''):
    """ Recursively extracts text from ``element`` (via _element_to_text), and
    wraps it all in ``wrapper``. Extracted text is added to ``output``

    :type wrapper: basestring | int
    """
    output.append(wrapper)
    if element.text:
        output.append(_collapse_whitespace(element.text))
    for child in element:
        _element_to_text(child, output)
    output.append(wrapper)


def _element_to_text(e, output):
    if e.tag == 'br':
        #output.append(u'\n')
        _wrap(e, output, 2)
    elif e.tag in _PADDED_BLOCK:
        _wrap(e, output, 1)
    elif e.tag in _MISC_BLOCK:
        _wrap(e, output, 1)
    else:
        # inline
        _wrap(e, output, 0)

    if e.tail and e.tail.strip():
        output.append(_collapse_whitespace(e.tail))
