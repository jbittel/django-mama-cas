.. _management-commands:

Management Commands
===================

django-mama-cas ships with custom management commands to aid in some common
tasks. You can see which management commands are available by running::

    manage.py

The commands specific to django-mama-cas will show up underneath the
``[mama_cas]`` heading. To run a given command::

    manage.py <command name>

Commands
--------

**cleanupcas**
   Tickets created by django-mama-cas are not removed from the database at the
   moment of invalidation. Running this command will delete all invalid
   tickets from the database. Tickets are invalidated either when they expire
   a configurable number of minutes after creation or by being consumed.
   Either situation means the ticket is no longer valid for future
   authentication attempts and can be safely deleted.

   It is recommended that this command be run on a regular basis so invalid
   tickets do not become a performance or storage concern.
