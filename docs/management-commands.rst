.. _management-commands:

Management commands
===================

django-mama-cas ships with management commands to aid in some common tasks.
You can see what custom managment commands are available by running::

    python manage.py

The commands specific to django-mama-cas will show up underneath the
``mama_cas`` heading. To run a given command::

    python manage.py <command name>

**cleanupcas**
   Tickets created by django-mama-cas are not removed from the database at
   the moment of invalidation. Running this command will delete all invalid
   tickets from the database. Tickets are invalidated either when they expire
   a configurable number of minutes after creation or by being consumed.
   Either situation means the ticket is no longer valid for future
   authentication attempts and can be safely deleted.

   It is recommended that this command be run on a regular basis so invalid
   tickets do not become a performance or storage concern.
