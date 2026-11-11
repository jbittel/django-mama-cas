from django.apps import AppConfig


class MamaCasConfig(AppConfig):
    name = 'mama_cas'
    verbose_name = 'MamaCAS'
    # Keep the primary key type used by the existing migrations, so
    # projects setting DEFAULT_AUTO_FIELD don't get a new migration
    # for mama_cas.
    default_auto_field = 'django.db.models.AutoField'
