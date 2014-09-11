import re

from django.core.urlresolvers import reverse

from mama_cas.compat import etree
from mama_cas.compat import urlencode


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


def build_url(name, **kwargs):
    """Build a URL given a view name and kwarg query parameters."""
    return reverse(name) + '?' + urlencode(kwargs)
