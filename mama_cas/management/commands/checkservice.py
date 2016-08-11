from django.core.management.base import BaseCommand

from mama_cas.services import get_callbacks
from mama_cas.services import get_logout_url
from mama_cas.services import logout_allowed
from mama_cas.services import proxy_allowed
from mama_cas.services import proxy_callback_allowed
from mama_cas.services import service_allowed


class Command(BaseCommand):
    help = 'Check validity and configuration of a service identifier'

    def add_arguments(self, parser):
        parser.add_argument(
            'service',
            help='Service identifier to check'
        )
        parser.add_argument(
            'pgturl', nargs='?',
            help='Optional pgtUrl to test proxy callback identifier'
        )

    def handle(self, **options):
        service = options['service']
        pgturl = options['pgturl']
        if service_allowed(service):
            self.stdout.write('Valid Service: %s' % service)
            self.stdout.write('Proxy Allowed: %s' % proxy_allowed(service))
            if pgturl:
                self.stdout.write('Proxy Callback Allowed: %s' % proxy_callback_allowed(service, pgturl))
            self.stdout.write('Logout Allowed: %s' % logout_allowed(service))
            self.stdout.write('Logout URL: %s' % get_logout_url(service))
            self.stdout.write('Callbacks: %s' % get_callbacks(service))
        else:
            self.stdout.write(self.style.ERROR('Invalid Service: %s' % service))
