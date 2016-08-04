from datetime import timedelta
from mock import patch

from django.contrib.auth import get_user_model
from django.utils.timezone import now

import factory

from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('username',)

    first_name = 'Ellen'
    last_name = 'Cohen'
    username = factory.LazyAttribute(lambda obj: obj.first_name.lower())
    email = factory.LazyAttribute(lambda obj: '%s@example.com' % obj.username)
    password = factory.PostGenerationMethodCall('set_password', 'mamas&papas')
    last_login = factory.LazyFunction(now)


class InactiveUserFactory(UserFactory):
    first_name = 'Denny'
    last_name = 'Doherty'
    is_active = False


class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True

    class Params:
        expire = factory.Trait(
            expires=factory.LazyAttribute(lambda obj: now() - timedelta(seconds=5))
        )
        consume = factory.Trait(
            consumed=factory.LazyFunction(now)
        )

    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        manager = cls._get_manager(target_class)
        return manager.create_ticket(*args, **kwargs)


class ServiceTicketFactory(TicketFactory):
    class Meta:
        model = ServiceTicket

    service = 'http://www.example.com/'


class ProxyGrantingTicketFactory(TicketFactory):
    class Meta:
        model = ProxyGrantingTicket

    granted_by_st = factory.SubFactory(ServiceTicketFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if not args:
            args = ('https://www.example.com/', 'https://www.example.com/callback')
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            return super(ProxyGrantingTicketFactory, cls)._create(target_class, *args, **kwargs)


class ProxyTicketFactory(TicketFactory):
    class Meta:
        model = ProxyTicket

    service = 'http://www.example.com/'
    granted_by_pgt = factory.SubFactory(ProxyGrantingTicketFactory)
