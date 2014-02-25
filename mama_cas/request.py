import datetime

from django.utils.crypto import get_random_string

from .compat import etree
from .compat import register_namespace


class CasRequestBase(object):
    """
    Base class for CAS 3.1 SAML format requests.
    """
    content_type = 'text/xml'
    prefixes = {}

    def __init__(self, context):
        self.context = context
        for prefix, uri in self.prefixes.items():
            register_namespace(prefix, uri)

    def ns(self, prefix, tag):
        """
        Given a prefix and an XML tag, output the qualified name
        for proper namespace handling on output.
        """
        return etree.QName(self.prefixes[prefix], tag)

    def headers(self):
        return {'content-type': self.content_type}


class SingleSignOutRequest(CasRequestBase):
    """
    [CAS 3.1] Render a SAML single sign-off request, to be sent to a
    service URL during a logout event.

    An example request:

    <samlp:LogoutRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="[RANDOM ID]"
    Version="2.0" IssueInstant="[CURRENT DATE/TIME]">
        <saml:NameID>@NOT_USED@</saml:NameID>
        <samlp:SessionIndex>[SESSION IDENTIFIER]</samlp:SessionIndex>
    </samlp:LogoutRequest>
    """
    prefixes = {'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
                'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'}

    def render_content(self):
        instant = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        ticket = self.context.get('ticket')

        logout_request = etree.Element(self.ns('samlp', 'LogoutRequest'))
        logout_request.set('ID', get_random_string(length=32))
        logout_request.set('Version', '2.0')
        logout_request.set('IssueInstant', instant)
        etree.SubElement(logout_request, self.ns('saml', 'NameID'))
        session_index = etree.SubElement(logout_request, self.ns('samlp', 'SessionIndex'))
        session_index.text = ticket.ticket

        return etree.tostring(logout_request, encoding='UTF-8')
