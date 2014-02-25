import re

from mama_cas.compat import etree


def parse(s):
    """
    Parse an XML tree from the given string, removing all
    of the included namespace strings.
    """
    ns = re.compile(r'^{.*?}')
    et = etree.fromstring(s)
    for elem in et.getiterator():
        elem.tag = ns.sub('', elem.tag)
    return et
